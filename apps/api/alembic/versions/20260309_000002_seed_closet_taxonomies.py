"""seed closet taxonomies

Revision ID: 20260309_000002
Revises: 20260309_000001
Create Date: 2026-03-09 14:30:00.000000
"""
from __future__ import annotations

import uuid

import sqlalchemy as sa

from alembic import op

revision = "20260309_000002"
down_revision = "20260309_000001"
branch_labels = None
depends_on = None


CATEGORY_SPECS = [
    ("tops", "Tops"),
    ("bottoms", "Bottoms"),
    ("outerwear", "Outerwear"),
    ("dresses_onepieces", "Dresses & One-Pieces"),
    ("footwear", "Footwear"),
    ("accessories", "Accessories"),
    ("activewear", "Activewear"),
]

SUBCATEGORY_SPECS = [
    ("tops", "t_shirt", "T-Shirt"),
    ("tops", "shirt", "Shirt"),
    ("tops", "blouse", "Blouse"),
    ("tops", "tank_top", "Tank Top"),
    ("tops", "sweater", "Sweater"),
    ("tops", "hoodie", "Hoodie"),
    ("bottoms", "jeans", "Jeans"),
    ("bottoms", "trousers", "Trousers"),
    ("bottoms", "shorts", "Shorts"),
    ("bottoms", "skirt", "Skirt"),
    ("bottoms", "leggings", "Leggings"),
    ("outerwear", "jacket", "Jacket"),
    ("outerwear", "coat", "Coat"),
    ("outerwear", "blazer", "Blazer"),
    ("outerwear", "cardigan", "Cardigan"),
    ("dresses_onepieces", "dress_mini", "Mini Dress"),
    ("dresses_onepieces", "dress_midi", "Midi Dress"),
    ("dresses_onepieces", "dress_maxi", "Maxi Dress"),
    ("dresses_onepieces", "jumpsuit", "Jumpsuit"),
    ("footwear", "sneakers", "Sneakers"),
    ("footwear", "boots", "Boots"),
    ("footwear", "heels", "Heels"),
    ("footwear", "flats", "Flats"),
    ("footwear", "sandals", "Sandals"),
    ("footwear", "loafers", "Loafers"),
    ("accessories", "bag", "Bag"),
    ("accessories", "belt", "Belt"),
    ("accessories", "hat", "Hat"),
    ("accessories", "scarf", "Scarf"),
    ("accessories", "jewelry", "Jewelry"),
    ("accessories", "watch", "Watch"),
    ("activewear", "sports_bra", "Sports Bra"),
    ("activewear", "workout_top", "Workout Top"),
    ("activewear", "joggers", "Joggers"),
    ("activewear", "track_jacket", "Track Jacket"),
]

COLOR_SPECS = [
    ("black", "Black"),
    ("white", "White"),
    ("gray", "Gray"),
    ("navy", "Navy"),
    ("blue", "Blue"),
    ("brown", "Brown"),
    ("beige", "Beige"),
    ("cream", "Cream"),
    ("green", "Green"),
    ("olive", "Olive"),
    ("yellow", "Yellow"),
    ("orange", "Orange"),
    ("red", "Red"),
    ("pink", "Pink"),
    ("purple", "Purple"),
    ("metallic", "Metallic"),
]

MATERIAL_SPECS = [
    ("cotton", "Cotton"),
    ("denim", "Denim"),
    ("wool", "Wool"),
    ("linen", "Linen"),
    ("silk", "Silk"),
    ("leather", "Leather"),
    ("faux_leather", "Faux Leather"),
    ("suede", "Suede"),
    ("polyester", "Polyester"),
    ("knit", "Knit"),
    ("cashmere", "Cashmere"),
]

PATTERN_SPECS = [
    ("solid", "Solid"),
    ("striped", "Striped"),
    ("plaid", "Plaid"),
    ("floral", "Floral"),
    ("polka_dot", "Polka Dot"),
    ("geometric", "Geometric"),
    ("animal_print", "Animal Print"),
    ("graphic", "Graphic"),
]

SEASON_SPECS = [
    ("spring", "Spring"),
    ("summer", "Summer"),
    ("autumn", "Autumn"),
    ("winter", "Winter"),
    ("all_season", "All Season"),
]

OCCASION_SPECS = [
    ("casual", "Casual"),
    ("work", "Work"),
    ("formal", "Formal"),
    ("party", "Party"),
    ("travel", "Travel"),
    ("lounge", "Lounge"),
    ("active", "Active"),
    ("date_night", "Date Night"),
]

FORMALITY_SPECS = [
    ("very_casual", "Very Casual", 1),
    ("casual", "Casual", 2),
    ("smart_casual", "Smart Casual", 3),
    ("business_casual", "Business Casual", 4),
    ("formal", "Formal", 5),
]

STYLE_SPECS = [
    ("minimalist", "Minimalist"),
    ("streetwear", "Streetwear"),
    ("classic", "Classic"),
    ("sporty", "Sporty"),
    ("chic", "Chic"),
    ("boho", "Boho"),
    ("edgy", "Edgy"),
    ("preppy", "Preppy"),
    ("vintage", "Vintage"),
    ("monochrome", "Monochrome"),
]


def _table(name: str, with_rank: bool = False) -> sa.Table:
    columns: list[sa.Column] = [
        sa.Column("id", sa.UUID()),
        sa.Column("slug", sa.String()),
        sa.Column("label", sa.String()),
    ]
    if with_rank:
        columns.append(sa.Column("rank", sa.Integer()))
    return sa.table(name, *columns)


def _rows(specs: list[tuple[str, str]]) -> list[dict[str, object]]:
    return [{"id": uuid.uuid4(), "slug": slug, "label": label} for slug, label in specs]


def upgrade() -> None:
    categories = _table("closet_categories")
    subcategories = sa.table(
        "closet_subcategories",
        sa.Column("id", sa.UUID()),
        sa.Column("category_id", sa.UUID()),
        sa.Column("slug", sa.String()),
        sa.Column("label", sa.String()),
    )
    colors = _table("closet_colors")
    materials = _table("closet_materials")
    patterns = _table("closet_patterns")
    seasons = _table("closet_seasons")
    occasions = _table("closet_occasions")
    formality_levels = _table("closet_formality_levels", with_rank=True)
    style_tags = _table("closet_style_tags")

    category_rows = _rows(CATEGORY_SPECS)
    category_ids = {str(row["slug"]): row["id"] for row in category_rows}

    op.bulk_insert(categories, category_rows)
    op.bulk_insert(
        subcategories,
        [
            {
                "id": uuid.uuid4(),
                "category_id": category_ids[category_slug],
                "slug": slug,
                "label": label,
            }
            for category_slug, slug, label in SUBCATEGORY_SPECS
        ],
    )
    op.bulk_insert(colors, _rows(COLOR_SPECS))
    op.bulk_insert(materials, _rows(MATERIAL_SPECS))
    op.bulk_insert(patterns, _rows(PATTERN_SPECS))
    op.bulk_insert(seasons, _rows(SEASON_SPECS))
    op.bulk_insert(occasions, _rows(OCCASION_SPECS))
    op.bulk_insert(
        formality_levels,
        [
            {"id": uuid.uuid4(), "slug": slug, "label": label, "rank": rank}
            for slug, label, rank in FORMALITY_SPECS
        ],
    )
    op.bulk_insert(style_tags, _rows(STYLE_SPECS))


def _delete_by_slugs(table_name: str, slugs: list[str]) -> None:
    bind = op.get_bind()
    bind.execute(
        sa.text(f"DELETE FROM {table_name} WHERE slug = ANY(:slugs)"),
        {"slugs": slugs},
    )


def downgrade() -> None:
    _delete_by_slugs("closet_style_tags", [slug for slug, _ in STYLE_SPECS])
    _delete_by_slugs("closet_formality_levels", [slug for slug, _, _ in FORMALITY_SPECS])
    _delete_by_slugs("closet_occasions", [slug for slug, _ in OCCASION_SPECS])
    _delete_by_slugs("closet_seasons", [slug for slug, _ in SEASON_SPECS])
    _delete_by_slugs("closet_patterns", [slug for slug, _ in PATTERN_SPECS])
    _delete_by_slugs("closet_materials", [slug for slug, _ in MATERIAL_SPECS])
    _delete_by_slugs("closet_colors", [slug for slug, _ in COLOR_SPECS])
    _delete_by_slugs("closet_subcategories", [slug for _, slug, _ in SUBCATEGORY_SPECS])
    _delete_by_slugs("closet_categories", [slug for slug, _ in CATEGORY_SPECS])
