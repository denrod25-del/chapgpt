"""Transactional email: Resend primary, Mailgun failover. Returns success bool."""
import logging
import httpx
from ..config import config

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


async def send_confirmation(to: str, name: str, service: str) -> bool:
    """Send lead confirmation. Tries Resend, then Mailgun. False if both fail."""
    if not to:
        return False
    html = _confirm_html(name, service, config.BRAND_PHONE)
    if await _resend(to, _CONFIRM_SUBJECT, html):
        return True
    log.warning("Resend failed for %s; trying Mailgun", to)
    return await _mailgun(to, _CONFIRM_SUBJECT, html)


async def _resend(to: str, subject: str, html: str) -> bool:
    if not config.RESEND_API_KEY:
        return False
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.post(
                "https://api.resend.com/emails",
                headers={"Authorization": f"Bearer {config.RESEND_API_KEY}"},
                json={"from": f"{config.BRAND} <hello@mail.whatsinyourwater.com>",
                      "to": [to], "subject": subject, "html": html},
            )
        return r.status_code < 300
    except httpx.HTTPError as e:
        log.error("Resend transport error: %s", e)
        return False


async def _mailgun(to: str, subject: str, html: str) -> bool:
    if not (config.MAILGUN_API_KEY and config.MAILGUN_DOMAIN):
        return False
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.post(
                f"https://api.mailgun.net/v3/{config.MAILGUN_DOMAIN}/messages",
                auth=("api", config.MAILGUN_API_KEY),
                data={"from": f"{config.BRAND} <hello@{config.MAILGUN_DOMAIN}>",
                      "to": to, "subject": subject, "html": html},
            )
        return r.status_code < 300
    except httpx.HTTPError as e:
        log.error("Mailgun transport error: %s", e)
        return False
