"""n8n-facing lifecycle automation endpoints. All INTERNAL_API_TOKEN gated and
guarded by the ENABLE_AUTOMATION_ENDPOINTS flag. Handlers stay thin."""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import require_internal
from app.core.config import settings
from app.deps import get_db
from app.schemas.automation import DeliveryUpdateOut, DeliveryUpdateRequest, DueAppointmentReminder
from app.schemas.review_request import (
    DueReviewRequest,
    MarkCompletedRequest,
    MarkFailedRequest,
    MarkSentRequest,
    ReviewRequestActionOut,
    ReviewRequestCreate,
    ReviewRequestOut,
)
from app.services import automation_service, review_request_service


async def require_automations_enabled() -> None:
    if not settings.ENABLE_AUTOMATION_ENDPOINTS:
        raise HTTPException(status_code=503, detail="automation endpoints are disabled")


router = APIRouter(
    prefix="/automations", tags=["automations"],
    dependencies=[Depends(require_internal), Depends(require_automations_enabled)],
)


# ── review requests ─────────────────────────────────────────────────────────
@router.post("/review-requests", response_model=ReviewRequestOut,
             status_code=status.HTTP_201_CREATED)
async def create_review_request(
    payload: ReviewRequestCreate, db: AsyncSession = Depends(get_db)
) -> ReviewRequestOut:
    return await review_request_service.create_review_request(db, payload)


@router.get("/review-requests/due", response_model=list[DueReviewRequest])
async def due_review_requests(
    limit: int = Query(default=100, ge=1, le=500), db: AsyncSession = Depends(get_db)
) -> list[DueReviewRequest]:
    return await review_request_service.fetch_due_review_requests(db, limit=limit)


@router.post("/review-requests/{review_request_id}/mark-sent",
             response_model=ReviewRequestActionOut)
async def mark_review_request_sent(
    review_request_id: uuid.UUID, payload: MarkSentRequest,
    db: AsyncSession = Depends(get_db),
) -> ReviewRequestActionOut:
    return await review_request_service.mark_review_request_sent(db, review_request_id, payload)


@router.post("/review-requests/{review_request_id}/mark-failed",
             response_model=ReviewRequestActionOut)
async def mark_review_request_failed(
    review_request_id: uuid.UUID, payload: MarkFailedRequest,
    db: AsyncSession = Depends(get_db),
) -> ReviewRequestActionOut:
    return await review_request_service.mark_review_request_failed(db, review_request_id, payload)


@router.post("/review-requests/{review_request_id}/mark-completed",
             response_model=ReviewRequestActionOut)
async def mark_review_request_completed(
    review_request_id: uuid.UUID, payload: MarkCompletedRequest,
    db: AsyncSession = Depends(get_db),
) -> ReviewRequestActionOut:
    return await review_request_service.mark_review_request_completed(
        db, review_request_id, payload
    )


# ── appointment reminders ───────────────────────────────────────────────────
@router.get("/appointment-reminders/due", response_model=list[DueAppointmentReminder])
async def due_appointment_reminders(
    limit: int = Query(default=100, ge=1, le=500), db: AsyncSession = Depends(get_db)
) -> list[DueAppointmentReminder]:
    return await automation_service.fetch_due_appointment_reminders(db, limit=limit)


# ── delivery posts ──────────────────────────────────────────────────────────
@router.post("/communications/{communication_log_id}/delivery-update",
             response_model=DeliveryUpdateOut)
async def post_delivery_update(
    communication_log_id: uuid.UUID, payload: DeliveryUpdateRequest,
    db: AsyncSession = Depends(get_db),
) -> DeliveryUpdateOut:
    return await automation_service.post_delivery_update(db, communication_log_id, payload)
