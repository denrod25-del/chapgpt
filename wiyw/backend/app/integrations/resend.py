"""Resend client — transactional email primary transport. Never raises."""
import logging

import httpx

from ..core.config import config

log = logging.getLogger("wiyw.resend")


async def send_email(to: str, subject: str, html: str) -> bool:
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
        if r.status_code >= 300:
            log.error("Resend %s: %s", r.status_code, r.text[:200])
        return r.status_code < 300
    except httpx.HTTPError as e:
        log.error("Resend transport error: %s", e)
        return False
