import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_db
from app.schemas.booking import BookingCreateRequest, BookingResponse
from app.services import booking_service

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.post("", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
async def create_booking(
    payload: BookingCreateRequest, db: AsyncSession = Depends(get_db)
) -> BookingResponse:
    return await booking_service.create_booking(db, payload)


@router.get("/{booking_id}", response_model=BookingResponse)
async def get_booking(
    booking_id: uuid.UUID, db: AsyncSession = Depends(get_db)
) -> BookingResponse:
    return await booking_service.get_booking(db, booking_id)
