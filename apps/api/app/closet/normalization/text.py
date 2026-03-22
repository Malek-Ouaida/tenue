from __future__ import annotations

import re

_NON_ALNUM_RE = re.compile(r"[^a-z0-9]+")


def normalize_lookup_key(value: str) -> str:
    lowered = value.strip().lower().replace("&", " and ")
    collapsed = _NON_ALNUM_RE.sub(" ", lowered)
    return " ".join(part for part in collapsed.split() if part)
