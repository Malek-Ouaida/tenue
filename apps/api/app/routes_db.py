from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.deps import get_db

router = APIRouter(prefix="/db", tags=["db"])


@router.get("/ping")
def ping(db: Annotated[Session, Depends(get_db)]) -> dict[str, Any]:
    v = db.execute(text("select 1")).scalar_one()
    return {"ok": True, "db": v}
