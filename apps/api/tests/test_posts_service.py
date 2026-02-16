from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.post_like import PostLike
from app.models.post_save import PostSave
from app.posts.service import (
    CreatePostMediaItem,
    PostError,
    create_comment,
    create_post,
    delete_comment,
    get_following_feed,
    like_post,
    save_post,
    unlike_post,
    unsave_post,
)
from app.users.follow_service import follow


def test_following_feed_contains_only_followed_accounts_and_self(
    db: Session,
    make_user,
    make_post,
) -> None:
    viewer = make_user("viewer_feed")
    followed = make_user("followed_feed")
    stranger = make_user("stranger_feed")

    follow(db, me_user_id=viewer.id, target_user_id=followed.id)

    make_post(viewer.id, "mine")
    make_post(followed.id, "followed")
    make_post(stranger.id, "stranger")

    items, _ = get_following_feed(db, viewer_user_id=viewer.id, cursor=None, limit=20)
    usernames = {item["author"]["username"] for item in items}

    assert "viewer_feed" in usernames
    assert "followed_feed" in usernames
    assert "stranger_feed" not in usernames


def test_pagination_is_stable_with_created_at_id_cursor(
    db: Session,
    make_user,
    make_post,
) -> None:
    viewer = make_user("viewer_page")
    same_time = datetime(2026, 1, 1, tzinfo=timezone.utc)

    p1 = uuid.UUID("00000000-0000-0000-0000-000000000001")
    p2 = uuid.UUID("00000000-0000-0000-0000-000000000002")
    p3 = uuid.UUID("00000000-0000-0000-0000-000000000003")

    make_post(viewer.id, "p1", created_at=same_time, post_id=p1)
    make_post(viewer.id, "p2", created_at=same_time, post_id=p2)
    make_post(viewer.id, "p3", created_at=same_time, post_id=p3)

    page_one, cursor = get_following_feed(db, viewer_user_id=viewer.id, cursor=None, limit=2)
    page_two, page_two_cursor = get_following_feed(db, viewer_user_id=viewer.id, cursor=cursor, limit=2)

    assert [item["id"] for item in page_one] == [str(p3), str(p2)]
    assert [item["id"] for item in page_two] == [str(p1)]
    assert cursor is not None
    assert page_two_cursor is None


def test_like_and_save_are_idempotent(
    db: Session,
    make_user,
) -> None:
    author = make_user("author_like")
    viewer = make_user("viewer_like")

    post = create_post(
        db,
        viewer_user_id=author.id,
        caption="hello",
        media_items=[
            CreatePostMediaItem(
                key="uploads/like-save.jpg",
                width=100,
                height=200,
                order=0,
            )
        ],
    )
    post_id = uuid.UUID(post["id"])

    like_post(db, post_id=post_id, viewer_user_id=viewer.id)
    like_post(db, post_id=post_id, viewer_user_id=viewer.id)
    save_post(db, post_id=post_id, viewer_user_id=viewer.id)
    save_post(db, post_id=post_id, viewer_user_id=viewer.id)

    like_count = db.execute(
        select(func.count()).select_from(PostLike).where(PostLike.post_id == post_id, PostLike.user_id == viewer.id)
    ).scalar_one()
    save_count = db.execute(
        select(func.count()).select_from(PostSave).where(PostSave.post_id == post_id, PostSave.user_id == viewer.id)
    ).scalar_one()

    assert int(like_count) == 1
    assert int(save_count) == 1

    unlike_post(db, post_id=post_id, viewer_user_id=viewer.id)
    unlike_post(db, post_id=post_id, viewer_user_id=viewer.id)
    unsave_post(db, post_id=post_id, viewer_user_id=viewer.id)
    unsave_post(db, post_id=post_id, viewer_user_id=viewer.id)

    like_count_after = db.execute(
        select(func.count()).select_from(PostLike).where(PostLike.post_id == post_id, PostLike.user_id == viewer.id)
    ).scalar_one()
    save_count_after = db.execute(
        select(func.count()).select_from(PostSave).where(PostSave.post_id == post_id, PostSave.user_id == viewer.id)
    ).scalar_one()

    assert int(like_count_after) == 0
    assert int(save_count_after) == 0


def test_comment_delete_requires_owner(
    db: Session,
    make_user,
) -> None:
    author = make_user("author_comment")
    commenter = make_user("commenter_comment")
    other = make_user("other_comment")

    post = create_post(
        db,
        viewer_user_id=author.id,
        caption="post",
        media_items=[
            CreatePostMediaItem(
                key="uploads/comments.jpg",
                width=100,
                height=100,
                order=0,
            )
        ],
    )
    post_id = uuid.UUID(post["id"])

    created = create_comment(db, post_id=post_id, viewer_user_id=commenter.id, body="hello")
    comment_id = uuid.UUID(created["id"])

    with pytest.raises(PostError) as forbidden_err:
        delete_comment(db, comment_id=comment_id, viewer_user_id=other.id)
    assert forbidden_err.value.code == "forbidden"

    delete_comment(db, comment_id=comment_id, viewer_user_id=commenter.id)

    with pytest.raises(PostError) as not_found_err:
        delete_comment(db, comment_id=comment_id, viewer_user_id=commenter.id)
    assert not_found_err.value.code == "comment_not_found"
