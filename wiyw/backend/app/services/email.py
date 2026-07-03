"""Transactional email service: Resend primary, Mailgun failover, templates.
Callers never pick Mailgun — failover is this service's decision (docs/OWNERSHIP.md)."""
import logging
from typing import Optional

from ..core.config import config
from ..integrations import mailgun, resend

log = logging.getLogger("wiyw.email")

_CONFIRM_SUBJECT = f"We got your request — {config.BRAND} is on it"


def _confirm_html(name: str, service: str, phone: str) -> str:
    return (
        f"<p>Hi {name},</p>"
        f"<p>Thanks for reaching out to {config.BRAND}. We've received your "
        f"request for <strong>{service.replace('_', ' ')}</strong>. A member of "
        f"our team will call you shortly during business hours.</p>"
        f"<p>Need us now? Call <a href='tel:{phone}'>{phone}</a> anytime.</p>"
        f"<p>— {config.BRAND} · Licensed &amp; insured · Serving Palm Beach County</p>"
    )


def review_request_html(name: str, review_link: str) -> str:
    return (
        f"<p>Hi {name},</p>"
        f"<p>Thanks for choosing {config.BRAND}! If you have 60 seconds, a quick "
        f"review helps other Palm Beach County homeowners find us:</p>"
        f"<p><a href='{review_link}'>Leave a review</a></p>"
        f"<p>— {config.BRAND}</p>"
    )


async def send(to: str, subject: str, html: str) -> tuple[bool, Optional[str]]:
    """Send a transactional email. Returns (success, winning_provider)."""
    if not to:
        return False, None
    if await resend.send_email(to, subject, html):
        return True, "resend"
    log.warning("Resend failed for %s; trying Mailgun", to)
    if await mailgun.send_email(to, subject, html):
        return True, "mailgun"
    return False, None


async def send_confirmation(to: str, name: str, service: str) -> bool:
    """Send lead/booking confirmation. Tries Resend, then Mailgun. False if both fail."""
    ok, _ = await send(to, _CONFIRM_SUBJECT, _confirm_html(name, service, config.BRAND_PHONE))
    return ok
