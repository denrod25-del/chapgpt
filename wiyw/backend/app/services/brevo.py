"""Brevo contact sync. Marketing source of truth for contacts."""
import logging
from typing import Optional
import httpx
from ..config import config

log = logging.getLogger("wiyw.brevo")


async def upsert_contact(email: Optional[str], phone: str, attrs: dict) -> Optional[str]:
    """Upsert a Brevo contact. Returns contact id or None. Never raises."""
    if not config.BREVO_API_KEY:
        return None
    if not (email or phone):
        return None
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.post(
                "https://api.brevo.com/v3/contacts",
                headers={"api-key": config.BREVO_API_KEY,
                         "content-type": "application/json"},
                json={"email": email, "sms": phone, "updateEnabled": True,
                      "attributes": attrs, "listIds": [2]},  # list_leads
            )
        if r.status_code in (200, 201, 204):
            body = r.json() if r.content else {}
            return str(body.get("id")) if body.get("id") else "upserted"
        log.error("Brevo %s: %s", r.status_code, r.text[:200])
        return None
    except httpx.HTTPError as e:
        log.error("Brevo transport error: %s", e)
        return None
