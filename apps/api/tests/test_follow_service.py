from __future__ import annotations

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.user_follow import UserFollow
from app.users.follow_service import FollowError, follow


def test_follow_uniqueness_and_self_follow_blocked(db: Session, make_user) -> None:
    me = make_user("follow_me")
    target = make_user("follow_target")

    first = follow(db, me_user_id=me.id, target_user_id=target.id)
    second = follow(db, me_user_id=me.id, target_user_id=target.id)

    edge_count = db.execute(
        select(func.count()).select_from(UserFollow).where(
            UserFollow.follower_user_id == me.id,
            UserFollow.following_user_id == target.id,
        )
    ).scalar_one()

    assert first == "followed"
    assert second == "already_following"
    assert int(edge_count) == 1

    with pytest.raises(FollowError) as self_follow_err:
        follow(db, me_user_id=me.id, target_user_id=me.id)
    assert self_follow_err.value.code == "cannot_follow_self"
