"""Mailgun client — transactional email FAILOVER transport (+ inbound parse domain).
Never a campaign sender; never the primary (docs/OWNERSHIP.md). Never raises."""
import logging

import httpx

from ..core.config import config

log = logging.getLogger("wiyw.mailgun")


async def send_email(to: str, subject: str, html: str) -> bool:
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
        if r.status_code >= 300:
            log.error("Mailgun %s: %s", r.status_code, r.text[:200])
        return r.status_code < 300
    except httpx.HTTPError as e:
        log.error("Mailgun transport error: %s", e)
        return False
