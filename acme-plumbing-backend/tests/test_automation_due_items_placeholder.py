"""Canonical mapping + delivery reconciliation.

Pure-unit mapping assertions run everywhere. The reconciliation-updates-a-
communication_log scenario runs only with RUN_DB_TESTS=1 against a migrated DB.
"""
import asyncio
import os
import uuid

import pytest

from app.schemas.provider_events import map_provider_event, should_apply_status

DB_TESTS = os.getenv("RUN_DB_TESTS") == "1"
SEED_BRAND_SLUG = "acme-plumbing"


# ── canonical mapping (pure unit) ────────────────────────────────────────────
def test_mailgun_permanent_fail_is_hard_bounce():
    event, status, flags = map_provider_event("mailgun", "failed", severity="permanent")
    assert event == "email_hard_bounced"
    assert status == "hard_bounce"
    assert "b" in flags


def test_mailgun_temporary_fail_is_deferred():
    event, status, _ = map_provider_event("mailgun", "failed", severity="temporary")
    assert event == "email_deferred"
    assert status == "deferred"


def test_gatewayapi_delivered_and_failed():
    assert map_provider_event("gatewayapi", "DELIVERED")[1] == "delivered"
    assert map_provider_event("gatewayapi", "UNDELIVERABLE")[1] == "failed"


def test_unknown_event_does_not_crash():
    event, status, flags = map_provider_event("brevo", "some_new_event")
    assert event == "email_some_new_event"
    assert status is None and flags == ""


def test_forward_only_status_progression():
    # 'sent' must not overwrite 'delivered'; a bounce always wins.
    assert should_apply_status("delivered", "sent") is False
    assert should_apply_status("sent", "delivered") is True
    assert should_apply_status("delivered", "hard_bounce") is True
    assert should_apply_status(None, "sent") is True


# ── reconciliation writes to communication_logs (opt-in DB) ──────────────────
@pytest.mark.skipif(not DB_TESTS, reason="set RUN_DB_TESTS=1 with a migrated DB")
def test_reconciliation_updates_communication_log():
    from app.db.session import SessionLocal, engine
    from app.repositories import comm_repository, communication_repository, get_brand_id_by_slug
    from app.schemas.provider_events import NormalizedEvent
    from app.services import delivery_reconciliation_service

    async def _run():
        try:
            ext_id = f"recon-{uuid.uuid4().hex[:10]}"
            async with SessionLocal() as db:
                brand_id = await get_brand_id_by_slug(db, SEED_BRAND_SLUG)
                row = await comm_repository.create(
                    db, brand_id=brand_id, channel="email", provider="mailgun",
                    template_key="txn_test", delivery_status="sent",
                    external_message_id=ext_id,
                )
                await db.commit()
                comm_id = row.id

            async with SessionLocal() as db:
                res = await delivery_reconciliation_service.reconcile(
                    db, NormalizedEvent(
                        provider="mailgun", provider_event="delivered",
                        canonical_event="email_delivered", delivery_status="delivered",
                        external_message_id=ext_id,
                    ),
                )
                await db.commit()
                assert res.matched is True
                assert res.delivery_updated is True
                assert res.event_logged is True

            async with SessionLocal() as db:
                updated = await communication_repository.get_by_id(db, comm_id)
                assert updated.delivery_status == "delivered"
                assert updated.delivered_at is not None
        finally:
            await engine.dispose()

    asyncio.run(_run())
