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
    get_saved_posts,
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


def test_following_feed_order_desc_created_at_then_id(
    db: Session,
    make_user,
    make_post,
) -> None:
    viewer = make_user("viewer_order")
    t0 = datetime(2026, 1, 1, tzinfo=timezone.utc)

    older = uuid.UUID("10000000-0000-0000-0000-000000000001")
    newer_small_id = uuid.UUID("10000000-0000-0000-0000-000000000010")
    newer_big_id = uuid.UUID("10000000-0000-0000-0000-000000000011")

    make_post(viewer.id, "older", created_at=t0, post_id=older)
    make_post(viewer.id, "newer_small", created_at=t0.replace(hour=1), post_id=newer_small_id)
    make_post(viewer.id, "newer_big", created_at=t0.replace(hour=1), post_id=newer_big_id)

    items, _ = get_following_feed(db, viewer_user_id=viewer.id, cursor=None, limit=20)
    assert [item["id"] for item in items] == [
        str(newer_big_id),
        str(newer_small_id),
        str(older),
    ]


def test_following_feed_includes_interaction_counts_and_flags(
    db: Session,
    make_user,
) -> None:
    author = make_user("author_counts")
    viewer = make_user("viewer_counts")
    commenter = make_user("commenter_counts")

    created = create_post(
        db,
        viewer_user_id=author.id,
        caption="count me",
        media_items=[CreatePostMediaItem(key="uploads/counts.jpg", width=800, height=1000, order=0)],
    )
    post_id = uuid.UUID(created["id"])

    like_post(db, post_id=post_id, viewer_user_id=viewer.id)
    like_post(db, post_id=post_id, viewer_user_id=commenter.id)
    save_post(db, post_id=post_id, viewer_user_id=viewer.id)
    create_comment(db, post_id=post_id, viewer_user_id=viewer.id, body="first")
    create_comment(db, post_id=post_id, viewer_user_id=commenter.id, body="second")

    items, _ = get_following_feed(db, viewer_user_id=viewer.id, cursor=None, limit=20)
    target = next(item for item in items if item["id"] == str(post_id))

    assert target["like_count"] == 2
    assert target["comment_count"] == 2
    assert target["viewer_liked"] is True
    assert target["viewer_saved"] is True


def test_saved_posts_cursor_pagination_is_stable(
    db: Session,
    make_user,
) -> None:
    viewer = make_user("viewer_saved")

    p1 = create_post(
        db,
        viewer_user_id=viewer.id,
        caption="p1",
        media_items=[CreatePostMediaItem(key="uploads/s1.jpg", width=100, height=100, order=0)],
    )
    p2 = create_post(
        db,
        viewer_user_id=viewer.id,
        caption="p2",
        media_items=[CreatePostMediaItem(key="uploads/s2.jpg", width=100, height=100, order=0)],
    )
    p3 = create_post(
        db,
        viewer_user_id=viewer.id,
        caption="p3",
        media_items=[CreatePostMediaItem(key="uploads/s3.jpg", width=100, height=100, order=0)],
    )

    save_post(db, post_id=uuid.UUID(p1["id"]), viewer_user_id=viewer.id)
    save_post(db, post_id=uuid.UUID(p2["id"]), viewer_user_id=viewer.id)
    save_post(db, post_id=uuid.UUID(p3["id"]), viewer_user_id=viewer.id)

    page_one, cursor = get_saved_posts(db, viewer_user_id=viewer.id, cursor=None, limit=2)
    page_two, second_cursor = get_saved_posts(db, viewer_user_id=viewer.id, cursor=cursor, limit=2)

    assert len(page_one) == 2
    assert len(page_two) == 1
    assert cursor is not None
    assert second_cursor is None
