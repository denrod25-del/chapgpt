from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_db
from app.schemas.lead import LeadCreateRequest, LeadCreateResponse
from app.services import lead_service

router = APIRouter(prefix="/leads", tags=["leads"])


@router.post("", response_model=LeadCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_lead(
    payload: LeadCreateRequest, db: AsyncSession = Depends(get_db)
) -> LeadCreateResponse:
    """Website lead / quote request intake (quote requests use lead_type=quote_request)."""
    return await lead_service.create_lead(db, payload)
