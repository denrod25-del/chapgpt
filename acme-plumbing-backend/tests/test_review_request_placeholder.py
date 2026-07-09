"""Review-request scheduling.

Pure-unit assertions run everywhere. The end-to-end DB flow (create → due →
mark-sent) runs only when RUN_DB_TESTS=1 and DATABASE_URL points at a migrated
DB (migrations 001 + 002 applied); otherwise it is skipped, not failed.
"""
import asyncio
import os
import uuid

import pytest

from app.schemas.common import ReviewRequestStatus
from app.schemas.review_request import ReviewRequestCreate

DB_TESTS = os.getenv("RUN_DB_TESTS") == "1"
SEED_BRAND_SLUG = "acme-plumbing"


# ── pure unit ───────────────────────────────────────────────────────────────
def test_create_schema_defaults():
    req = ReviewRequestCreate(contact_id=uuid.uuid4())
    assert req.brand_slug == "acme-plumbing"
    assert req.channel == "sms"
    assert req.review_url is None       # service fills settings.DEFAULT_REVIEW_URL
    assert req.delay_minutes is None    # service fills the default delay


def test_status_vocabulary_matches_migration_check():
    assert {s.value for s in ReviewRequestStatus} == {
        "pending", "due", "sent", "delivered", "clicked",
        "completed", "failed", "canceled",
    }


# ── DB-backed end-to-end (opt-in) ────────────────────────────────────────────
@pytest.mark.skipif(not DB_TESTS, reason="set RUN_DB_TESTS=1 with a migrated DB")
def test_due_endpoint_fields_and_mark_sent():
    from app.db.session import SessionLocal, engine
    from app.repositories import get_or_create_contact, get_brand_id_by_slug
    from app.schemas.review_request import MarkSentRequest
    from app.services import review_request_service

    async def _run():
        # Dispose the pool inside this loop (a later asyncio.run would otherwise
        # try to terminate these connections on a closed loop).
        try:
            async with SessionLocal() as db:
                brand_id = await get_brand_id_by_slug(db, SEED_BRAND_SLUG)
                assert brand_id is not None
                contact = await get_or_create_contact(
                    db, brand_id=brand_id, first_name="Rev", last_name=None,
                    email=f"rev-{uuid.uuid4().hex[:8]}@example.com", phone=None,
                    source="test",
                )
                await db.commit()
                created = await review_request_service.create_review_request(
                    db, ReviewRequestCreate(contact_id=contact.id, delay_minutes=0)
                )
                assert created.status == "pending"

            async with SessionLocal() as db:
                due = await review_request_service.fetch_due_review_requests(db, limit=50)
                match = [d for d in due if d.id == created.id]
                assert match, "created request should be due (delay 0)"
                item = match[0]
                # DueReviewRequest carries enough context for an SMS/email send.
                assert item.review_url and item.channel == "sms"
                assert item.first_name == "Rev"

            async with SessionLocal() as db:
                out = await review_request_service.mark_review_request_sent(
                    db, created.id, MarkSentRequest(external_message_id="msg-123")
                )
                assert out.status == "sent"
        finally:
            await engine.dispose()

    asyncio.run(_run())


@pytest.mark.skipif(not DB_TESTS, reason="set RUN_DB_TESTS=1 with a migrated DB")
def test_due_skips_cancelled_booking():
    """A review request linked to a cancelled booking must not be dispatched."""
    import datetime as dt

    from sqlalchemy import update

    from app.db.session import SessionLocal, engine
    from app.models.booking import Booking
    from app.repositories import get_or_create_contact, get_brand_id_by_slug
    from app.repositories import review_request_repository as rr_repo
    from app.schemas.booking import BookingCreateRequest
    from app.schemas.review_request import ReviewRequestCreate
    from app.services import booking_service, review_request_service

    async def _run():
        try:
            async with SessionLocal() as db:
                brand_id = await get_brand_id_by_slug(db, SEED_BRAND_SLUG)
                contact = await get_or_create_contact(
                    db, brand_id=brand_id, first_name="Cxl", last_name=None,
                    email=f"cxl-{uuid.uuid4().hex[:8]}@example.com", phone=None,
                    source="test",
                )
                await db.commit()
                soon = dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=2)
                booking = await booking_service.create_booking(
                    db, BookingCreateRequest(
                        first_name="Cxl", email=contact.email, scheduled_for=soon)
                )
                req = await review_request_service.create_review_request(
                    db, ReviewRequestCreate(
                        contact_id=contact.id, booking_id=booking.id,
                        delay_minutes=0, channel="email")
                )

            async with SessionLocal() as db:
                due_ids = {r.id for r, _ in await rr_repo.fetch_due(db, limit=500)}
                assert req.id in due_ids, "should be due before cancellation"

            async with SessionLocal() as db:
                await db.execute(update(Booking).where(Booking.id == booking.id)
                                 .values(booking_status="cancelled"))
                await db.commit()

            async with SessionLocal() as db:
                due_ids = {r.id for r, _ in await rr_repo.fetch_due(db, limit=500)}
                assert req.id not in due_ids, "cancelled booking must be skipped"
        finally:
            await engine.dispose()

    asyncio.run(_run())
