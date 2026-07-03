from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_db
from app.schemas.event import EventCreateRequest, EventResponse
from app.services import event_service

router = APIRouter(prefix="/events", tags=["events"])


@router.post("", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def record_event(
    payload: EventCreateRequest, db: AsyncSession = Depends(get_db)
) -> EventResponse:
    """Frontend/system event ingestion (page views, call clicks, form starts…)."""
    return await event_service.record_event(db, payload)
