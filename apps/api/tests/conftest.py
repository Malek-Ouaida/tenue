from __future__ import annotations

import uuid
from collections.abc import Callable, Generator
from datetime import datetime, timezone

import pytest
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session, sessionmaker

from app.db import engine
from app.models.post import Post
from app.models.post_media import PostMedia
from app.models.user import User
from app.models.user_profile import UserProfile


@pytest.fixture
def db() -> Generator[Session, None, None]:
    try:
        connection = engine.connect()
    except OperationalError as e:
        pytest.skip(f"Database unavailable for integration tests: {e}")

    transaction = connection.begin()
    test_session = sessionmaker(
        bind=connection,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )
    session = test_session()

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def make_user(db: Session) -> Callable[[str], User]:
    counter = {"value": 0}

    def _make_user(username: str) -> User:
        counter["value"] += 1
        email = f"{username}-{counter['value']}@example.com"

        user = User(id=uuid.uuid4(), email=email, hashed_password="x" * 60)
        profile = UserProfile(
            user_id=user.id,
            username=username,
            display_name=username.title(),
        )
        db.add(user)
        db.add(profile)
        db.commit()
        return user

    return _make_user


@pytest.fixture
def make_post(db: Session) -> Callable[[uuid.UUID, str, datetime | None, uuid.UUID | None], Post]:
    def _make_post(
        author_id: uuid.UUID,
        caption: str,
        created_at: datetime | None = None,
        post_id: uuid.UUID | None = None,
    ) -> Post:
        post_uuid = post_id or uuid.uuid4()
        timestamp = created_at or datetime.now(timezone.utc)

        post = Post(
            id=post_uuid,
            author_id=author_id,
            caption=caption,
            created_at=timestamp,
            updated_at=timestamp,
        )
        media = PostMedia(
            id=uuid.uuid4(),
            post_id=post_uuid,
            key=f"uploads/{post_uuid}.jpg",
            width=1200,
            height=1600,
            order=0,
        )
        db.add(post)
        db.add(media)
        db.commit()
        return post

    return _make_post
