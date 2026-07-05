"""Brevo webhook parsing + verification policy (pure unit; no DB)."""
from app.services import brevo_webhook_service


def test_brevo_delivered_maps_to_canonical():
    payload = {
        "event": "delivered",
        "email": "customer@example.com",
        "message-id": "<abc@relay>",
        "tags": ["txn_lead_confirmation"],
        "ts": 1700000000,
    }
    events = brevo_webhook_service.parse_events(payload)
    assert len(events) == 1
    ev = events[0]
    assert ev.provider == "brevo"
    assert ev.canonical_event == "email_delivered"
    assert ev.delivery_status == "delivered"
    assert ev.external_message_id == "<abc@relay>"
    assert ev.email == "customer@example.com"
    assert ev.tags == ["txn_lead_confirmation"]


def test_brevo_hardbounce_sets_bounce_flag():
    events = brevo_webhook_service.parse_events(
        {"event": "hardBounce", "email": "x@y.com", "message-id": "m1"}
    )
    ev = events[0]
    assert ev.canonical_event == "email_hard_bounced"
    assert ev.delivery_status == "hard_bounce"
    assert ev.is_bounce is True


def test_brevo_unsubscribe_sets_flag():
    events = brevo_webhook_service.parse_events(
        {"event": "unsubscribed", "email": "x@y.com"}
    )
    assert events[0].is_unsubscribe is True
    assert events[0].canonical_event == "contact_unsubscribed"


def test_brevo_opened_does_not_change_delivery_status():
    ev = brevo_webhook_service.parse_events({"event": "opened", "email": "x@y.com"})[0]
    assert ev.canonical_event == "email_opened"
    assert ev.delivery_status is None


def test_brevo_empty_payload_yields_no_events():
    assert brevo_webhook_service.parse_events({}) == []


def test_brevo_verification_unverified_without_secret():
    # No BREVO_WEBHOOK_SECRET configured → 'unverified' (Brevo has no HMAC).
    status = brevo_webhook_service.verification_status({}, {"event": "delivered"})
    assert status == "unverified"
