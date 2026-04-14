from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health() -> dict:
    return {"ok": True, "status": "healthy"}

