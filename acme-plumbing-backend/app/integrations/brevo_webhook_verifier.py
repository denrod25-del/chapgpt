"""Brevo webhook authenticity.

Brevo has no native HMAC signing. Its webhooks can be configured with custom
headers/auth, so the verifiable option is a shared secret that Brevo sends back —
commonly as a custom header (e.g. `X-Sib-Webhook-Secret`) or a query token that
gets surfaced in the payload. We compare it in constant time when configured; if
no secret is configured we store the payload and mark it 'unverified' (we do NOT
pretend it is cryptographically authenticated).
"""
import hmac
from typing import Mapping, Optional

from app.core.config import settings

_SECRET_HEADERS = ("x-sib-webhook-secret", "x-brevo-webhook-secret", "x-webhook-secret")


def _presented_secret(headers: Mapping[str, str], payload: dict) -> Optional[str]:
    lowered = {k.lower(): v for k, v in headers.items()}
    for name in _SECRET_HEADERS:
        if lowered.get(name):
            return lowered[name]
    # Fall back to a secret echoed in the body (configurable webhook field).
    token = payload.get("webhook_secret") or payload.get("secret")
    return token if isinstance(token, str) else None


def verify(headers: Mapping[str, str], payload: dict, *, secret: Optional[str] = None) -> bool:
    expected = secret if secret is not None else settings.BREVO_WEBHOOK_SECRET
    if not expected:
        return False
    presented = _presented_secret(headers, payload)
    if not presented:
        return False
    return hmac.compare_digest(presented, expected)


def verification_status(headers: Mapping[str, str], payload: dict) -> str:
    """'unverified' when no secret is configured (Brevo has no HMAC);
    verified/invalid when a secret is configured and compared."""
    if not settings.BREVO_WEBHOOK_SECRET:
        return "unverified"
    return "verified" if verify(headers, payload) else "invalid"
