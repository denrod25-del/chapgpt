"""Review-request route (n8n workflow 05). Bearer-auth protected."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import require_internal
from app.deps import get_db
from app.schemas.review import ReviewRequestOut, ReviewRequestPayload
from app.services import review_service

router = APIRouter(prefix="/reviews", tags=["reviews"],
                   dependencies=[Depends(require_internal)])


@router.post("/request", response_model=ReviewRequestOut)
async def request_review(
    payload: ReviewRequestPayload, db: AsyncSession = Depends(get_db)
) -> ReviewRequestOut:
    return await review_service.request_review(db, payload)
