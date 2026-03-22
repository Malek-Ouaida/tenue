from __future__ import annotations

AUTO_ACCEPT_CONFIDENCE = 0.80
REVIEW_CONFIDENCE = 0.55
IMPLICIT_CONFIDENCE = 0.70

CATEGORY_SYNONYMS = {
    "top": "tops",
    "bottom": "bottoms",
    "outer layer": "outerwear",
    "one piece": "dresses_onepieces",
    "one pieces": "dresses_onepieces",
    "dress": "dresses_onepieces",
    "shoe": "footwear",
    "shoes": "footwear",
    "accessory": "accessories",
    "athleisure": "activewear",
}

SUBCATEGORY_SYNONYMS = {
    "tee": "t_shirt",
    "t shirt": "t_shirt",
    "tshirt": "t_shirt",
    "button down": "shirt",
    "button up": "shirt",
    "cami": "tank_top",
    "camisole": "tank_top",
    "jumper": "sweater",
    "pullover": "sweater",
    "sweatshirt": "hoodie",
    "pants": "trousers",
    "pant": "trousers",
    "slacks": "trousers",
    "chinos": "trousers",
    "jean": "jeans",
    "denim pants": "jeans",
    "mini dress": "dress_mini",
    "minidress": "dress_mini",
    "midi dress": "dress_midi",
    "mididress": "dress_midi",
    "maxi dress": "dress_maxi",
    "maxidress": "dress_maxi",
    "trainer": "sneakers",
    "trainers": "sneakers",
    "pump": "heels",
    "pumps": "heels",
    "handbag": "bag",
    "purse": "bag",
    "crossbody": "bag",
    "cross body": "bag",
    "tote": "bag",
    "jewellery": "jewelry",
    "necklace": "jewelry",
    "bracelet": "jewelry",
    "earrings": "jewelry",
    "active top": "workout_top",
    "running top": "workout_top",
    "track pants": "joggers",
    "sweatpants": "joggers",
}

COLOR_SYNONYMS = {
    "grey": "gray",
    "off white": "cream",
    "offwhite": "cream",
    "ivory": "cream",
    "tan": "beige",
    "burgundy": "red",
    "maroon": "red",
}

MATERIAL_SYNONYMS = {
    "jean": "denim",
    "vegan leather": "faux_leather",
    "fake leather": "faux_leather",
    "pu leather": "faux_leather",
}

PATTERN_SYNONYMS = {
    "check": "plaid",
    "checked": "plaid",
    "checkered": "plaid",
    "tartan": "plaid",
    "dots": "polka_dot",
    "polka dots": "polka_dot",
    "leopard": "animal_print",
    "zebra": "animal_print",
    "snake": "animal_print",
}

SEASON_SYNONYMS = {
    "fall": "autumn",
    "all season": "all_season",
    "all seasons": "all_season",
}

OCCASION_SYNONYMS = {
    "night out": "party",
    "vacation": "travel",
    "holiday": "travel",
}

FORMALITY_SYNONYMS = {
    "very casual": "very_casual",
    "smart casual": "smart_casual",
    "business": "business_casual",
    "business casual": "business_casual",
}

STYLE_TAG_SYNONYMS = {
    "minimal": "minimalist",
    "sport": "sporty",
    "sportswear": "sporty",
    "retro": "vintage",
}

SLEEVE_LENGTH_SYNONYMS = {
    "no sleeves": "sleeveless",
    "short sleeve": "short",
    "short sleeves": "short",
    "3 4": "three_quarter",
    "3 4 sleeve": "three_quarter",
    "three quarter": "three_quarter",
    "three quarter sleeve": "three_quarter",
    "long sleeve": "long",
    "long sleeves": "long",
}

FIT_SYNONYMS = {
    "fitted": "slim",
    "straight": "regular",
    "loose": "relaxed",
    "baggy": "oversized",
}
