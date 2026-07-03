"""Brand dashboard summary — read-only KPI aggregates."""
from fastapi import APIRouter, Depends, HTTPException, Query

from ...core.auth import require_internal
from ...db.session import get_pool
from ...models import repo

router = APIRouter(prefix="/brands", tags=["dashboard"],
                   dependencies=[Depends(require_internal)])


@router.get("/{brand_id}/dashboard-summary")
async def dashboard_summary(brand_id: str,
                            window_days: int = Query(default=30, ge=1, le=365)) -> dict:
    pool = get_pool()
    async with pool.acquire() as conn:
        brand = await conn.fetchval("SELECT 1 FROM brands WHERE id=$1", brand_id)
        if not brand:
            raise HTTPException(404, "brand not found")
        summary = await repo.dashboard_summary(conn, brand_id, window_days)
    return {"brand_id": brand_id, "window_days": window_days, **summary}
