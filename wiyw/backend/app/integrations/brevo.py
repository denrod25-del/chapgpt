"""Brevo client — marketing contact mirror. Postgres stays the source of truth.
Failures are non-fatal everywhere: the mirror self-heals on the next sync."""
import logging
from typing import Optional, Union

import httpx

from ..core.config import config

log = logging.getLogger("wiyw.brevo")

Attrs = dict[str, Union[str, int, float, bool, None]]


async def upsert_contact(email: Optional[str], phone: str, attrs: Attrs,
                         list_ids: Optional[list[int]] = None) -> Optional[str]:
    """Upsert a Brevo contact. Returns contact id (or 'upserted') or None. Never raises."""
    if not config.BREVO_API_KEY:
        return None
    if not (email or phone):
        return None
    clean_attrs = {k: v for k, v in attrs.items() if v is not None}
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.post(
                "https://api.brevo.com/v3/contacts",
                headers={"api-key": config.BREVO_API_KEY,
                         "content-type": "application/json"},
                json={"email": email, "sms": phone, "updateEnabled": True,
                      "attributes": clean_attrs,
                      "listIds": list_ids or [config.BREVO_LIST_NEW_LEADS]},
            )
        if r.status_code in (200, 201, 204):
            body = r.json() if r.content else {}
            return str(body.get("id")) if body.get("id") else "upserted"
        log.error("Brevo %s: %s", r.status_code, r.text[:200])
        return None
    except httpx.HTTPError as e:
        log.error("Brevo transport error: %s", e)
        return None
