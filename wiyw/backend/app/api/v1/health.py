"""Liveness."""
from fastapi import APIRouter

from ...core.config import config

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict:
    return {"status": "ok", "brand": config.BRAND}
