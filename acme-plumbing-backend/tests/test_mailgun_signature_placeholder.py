"""Mailgun HMAC verification — valid and invalid signatures.

Pure unit; no DB. Run: pytest tests/test_mailgun_signature_placeholder.py
"""
import hashlib
import hmac

from app.integrations import mailgun_webhook_verifier

SIGNING_KEY = "test-signing-key"
TIMESTAMP = "1700000000"
TOKEN = "abc123token"


def _sign(key: str, timestamp: str, token: str) -> str:
    return hmac.new(
        key.encode(), f"{timestamp}{token}".encode(), hashlib.sha256
    ).hexdigest()


def test_valid_mailgun_signature_passes():
    sig = _sign(SIGNING_KEY, TIMESTAMP, TOKEN)
    assert mailgun_webhook_verifier.verify(
        timestamp=TIMESTAMP, token=TOKEN, signature=sig, signing_key=SIGNING_KEY
    ) is True


def test_invalid_mailgun_signature_fails():
    assert mailgun_webhook_verifier.verify(
        timestamp=TIMESTAMP, token=TOKEN, signature="deadbeef", signing_key=SIGNING_KEY
    ) is False


def test_tampered_timestamp_fails():
    sig = _sign(SIGNING_KEY, TIMESTAMP, TOKEN)
    assert mailgun_webhook_verifier.verify(
        timestamp="1700000001", token=TOKEN, signature=sig, signing_key=SIGNING_KEY
    ) is False


def test_missing_parts_fail():
    assert mailgun_webhook_verifier.verify(
        timestamp=None, token=TOKEN, signature="x", signing_key=SIGNING_KEY
    ) is False
    assert mailgun_webhook_verifier.verify(
        timestamp=TIMESTAMP, token=TOKEN, signature=None, signing_key=SIGNING_KEY
    ) is False


def test_verification_status_unconfigured_without_key():
    # settings default has no signing key → 'unconfigured', never a false 'verified'.
    payload = {"signature": {"timestamp": TIMESTAMP, "token": TOKEN, "signature": "x"}}
    assert mailgun_webhook_verifier.verification_status(payload) == "unconfigured"
