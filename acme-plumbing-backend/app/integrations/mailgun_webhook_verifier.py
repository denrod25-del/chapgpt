"""Mailgun webhook authenticity.

Mailgun signs each webhook: signature = HMAC-SHA256(key=signing_key,
msg=timestamp + token), hex-encoded. We recompute and compare in constant time.
The signature block lives in the JSON body under `signature`:
  {"signature": {"timestamp": "...", "token": "...", "signature": "..."}}
"""
import hashlib
import hmac
from typing import Optional

from app.core.config import settings


def extract_signature_block(payload: dict) -> dict:
    block = payload.get("signature")
    return block if isinstance(block, dict) else {}


def verify(
    *, timestamp: Optional[str], token: Optional[str], signature: Optional[str],
    signing_key: Optional[str] = None,
) -> bool:
    """True only if all parts are present and the HMAC matches. Never raises."""
    key = signing_key if signing_key is not None else settings.MAILGUN_WEBHOOK_SIGNING_KEY
    if not key or not timestamp or not token or not signature:
        return False
    try:
        computed = hmac.new(
            key.encode("utf-8"),
            msg=f"{timestamp}{token}".encode("utf-8"),
            digestmod=hashlib.sha256,
        ).hexdigest()
    except Exception:  # noqa: BLE001 — verification must never crash the receiver
        return False
    return hmac.compare_digest(computed, signature)


def verification_status(payload: dict) -> str:
    """Map a raw Mailgun payload to a verification_status value.
    'unconfigured' when no signing key is set (dev); otherwise verified/invalid."""
    if not settings.MAILGUN_WEBHOOK_SIGNING_KEY:
        return "unconfigured"
    block = extract_signature_block(payload)
    ok = verify(
        timestamp=block.get("timestamp"),
        token=block.get("token"),
        signature=block.get("signature"),
    )
    return "verified" if ok else "invalid"
