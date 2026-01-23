from __future__ import annotations

import argparse
import csv
import random
import string
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.auth import service as auth_service
from app.users.follow_service import follow as follow_user
from app.users.follow_service import FollowError
from app.users.service import ProfileError

# ---------
# Simple content pools (no external deps)
# ---------

ADJECTIVES = [
    "calm", "bold", "clean", "soft", "sharp", "urban", "cozy", "fresh", "sleek", "vivid",
    "minimal", "classic", "modern", "dreamy", "quiet", "wild", "bright", "neutral", "chic", "retro",
]
NOUNS = [
    "studio", "atelier", "thread", "wardrobe", "closet", "look", "style", "muse", "canvas", "pattern",
    "denim", "silk", "leather", "sneaker", "jacket", "ring", "watch", "scarf", "gallery", "archive",
]
FIRST_NAMES = [
    "Malek", "Nour", "Rami", "Maya", "Jad", "Lea", "Ali", "Sara", "Omar", "Lina",
    "Karim", "Hana", "Tarek", "Rana", "Ziad", "Dima", "Fadi", "Nada", "Samir", "Yara",
]
BIOS = [
    "saving outfits I love ✨",
    "fashion + tech.",
    "minimal fits, maximal energy.",
    "building tenue.",
    "collecting looks & inspiration.",
    "streetwear / classics / neutrals.",
    "archiving my style experiments.",
    "outfits, details, textures.",
    "style is a language.",
    "trying new silhouettes weekly.",
]


@dataclass(frozen=True)
class Cred:
    username: str
    email: str
    password: str
    display_name: str | None


def _slug(s: str) -> str:
    s = s.strip().lower()
    allowed = string.ascii_lowercase + string.digits + "_"
    out = []
    prev_us = False
    for ch in s:
        if ch in string.ascii_lowercase + string.digits:
            out.append(ch)
            prev_us = False
        elif ch in {" ", "-", ".", "/"}:
            if not prev_us and out:
                out.append("_")
                prev_us = True
        elif ch == "_":
            if not prev_us and out:
                out.append("_")
                prev_us = True
        # drop everything else
    slug = "".join(out).strip("_")
    while "__" in slug:
        slug = slug.replace("__", "_")
    return slug


def _make_username(rng: random.Random, taken: set[str]) -> str:
    # IG-style: adjective_noun + optional digit
    base = f"{rng.choice(ADJECTIVES)}_{rng.choice(NOUNS)}"
    base = _slug(base)[:20]
    if len(base) < 3:
        base = f"user_{rng.randint(100,999)}"

    candidate = base
    n = 0
    while candidate in taken or len(candidate) < 3:
        n += 1
        suffix = str(rng.randint(1, 9999))
        candidate = (base[: max(0, 20 - (len(suffix) + 1))] + "_" + suffix)[:20]
        if n > 5000:
            raise RuntimeError("Failed to generate unique usernames")
    taken.add(candidate)
    return candidate


def _make_display_name(rng: random.Random) -> str:
    return f"{rng.choice(FIRST_NAMES)} {rng.choice(FIRST_NAMES)}"


def _make_email(username: str, domain: str) -> str:
    return f"{username}@{domain}"


def _write_credentials(out_dir: Path, creds: list[Cred]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    csv_path = out_dir / "seed_credentials.csv"
    txt_path = out_dir / "seed_credentials.txt"

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["username", "email", "password", "display_name"])
        w.writeheader()
        for c in creds:
            w.writerow(
                {
                    "username": c.username,
                    "email": c.email,
                    "password": c.password,
                    "display_name": c.display_name or "",
                }
            )

    lines = []
    for c in creds:
        lines.append(f"{c.username} | {c.email} | {c.password}")
    txt_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Wrote: {csv_path}")
    print(f"Wrote: {txt_path}")


def _reset_social(db: Session) -> None:
    """
    Wipes social tables. Uses CASCADE from users -> profiles/follows/sessions/refresh tokens.
    Only run in local/dev.
    """
    # Order matters, but CASCADE should handle most.
    db.execute(text("TRUNCATE TABLE user_follows RESTART IDENTITY CASCADE"))
    db.execute(text("TRUNCATE TABLE user_profiles RESTART IDENTITY CASCADE"))
    db.execute(text("TRUNCATE TABLE auth_refresh_tokens RESTART IDENTITY CASCADE"))
    db.execute(text("TRUNCATE TABLE auth_sessions RESTART IDENTITY CASCADE"))
    db.execute(text("TRUNCATE TABLE users RESTART IDENTITY CASCADE"))
    db.commit()


def _seed_users(db: Session, *, count: int, password: str, domain: str, seed: int) -> list[Cred]:
    rng = random.Random(seed)
    taken: set[str] = set()
    creds: list[Cred] = []

    # Pre-take some obvious reserved-ish names just to avoid collisions in output.
    taken |= {"admin", "auth", "users", "me", "search"}

    for _ in range(count):
        username = _make_username(rng, taken)
        email = _make_email(username, domain)
        display_name = _make_display_name(rng)
        bio = rng.choice(BIOS)

        # Register using your auth service (creates profile at signup)
        try:
            user = auth_service.register(
                db=db,
                email=email,
                password=password,
                username=username,
                display_name=display_name,
            )
        except ProfileError as e:
            # Should be rare; if it happens, just keep going with a new username
            # (but we already track taken, so mostly defensive)
            continue
        except auth_service.AuthError:
            # email conflict or other constraint; skip
            continue

        # Optional: set bio after registration by updating profile directly
        # (If you prefer using service.update_my_profile, import and call it instead.)
        db.execute(
            text("UPDATE user_profiles SET bio = :bio WHERE user_id = :uid"),
            {"bio": bio, "uid": str(user.id)},
        )
        db.commit()

        creds.append(Cred(username=username, email=email, password=password, display_name=display_name))

    return creds


def _seed_follows(db: Session, *, creds: list[Cred], follows_per_user: int, seed: int) -> None:
    if not creds:
        return
    rng = random.Random(seed + 999)

    # Map username -> user_id
    rows = db.execute(text("SELECT user_id, username FROM user_profiles")).fetchall()
    by_username = {r[1]: r[0] for r in rows}

    usernames = list(by_username.keys())
    total = 0

    for u in usernames:
        me_id = by_username[u]
        targets = [x for x in usernames if x != u]
        rng.shuffle(targets)
        to_follow = targets[: min(follows_per_user, len(targets))]

        for t in to_follow:
            try:
                follow_user(db, me_user_id=me_id, target_user_id=by_username[t])
                total += 1
            except FollowError:
                # already following / invalid / etc.
                continue

    print(f"Seeded follow edges: ~{total}")


def main() -> None:
    p = argparse.ArgumentParser(description="Seed Tenue social graph (users + profiles + follows) + credentials files.")
    p.add_argument("--count", type=int, default=50, help="Number of users to create")
    p.add_argument("--follows-per-user", type=int, default=25, help="How many accounts each user follows")
    p.add_argument("--password", type=str, default="Password123!", help="Password for all seeded users")
    p.add_argument("--domain", type=str, default="tenue.dev", help="Email domain for seeded accounts")
    p.add_argument("--seed", type=int, default=42, help="Deterministic RNG seed")
    p.add_argument("--out", type=str, default="apps/api/seed", help="Output directory for credentials files")
    p.add_argument("--reset", action="store_true", help="Wipe social/auth tables before seeding (DEV ONLY)")
    args = p.parse_args()

    out_dir = Path(args.out)

    with SessionLocal() as db:
        if args.reset:
            _reset_social(db)
            print("Reset done.")

        creds = _seed_users(
            db,
            count=args.count,
            password=args.password,
            domain=args.domain,
            seed=args.seed,
        )

        # follows
        _seed_follows(
            db,
            creds=creds,
            follows_per_user=args.follows_per_user,
            seed=args.seed,
        )

    _write_credentials(out_dir, creds)
    print(f"Seeded users: {len(creds)}")


if __name__ == "__main__":
    main()
