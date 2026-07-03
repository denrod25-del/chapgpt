"""Brevo client — marketing contact mirror. Postgres stays the source of truth;
failures are non-fatal (the mirror self-heals on the next sync). Never raises."""
import logging
from typing import Optional, Union

import httpx

from app.core.config import settings

log = logging.getLogger("acme.brevo")

Attrs = dict[str, Union[str, int, float, bool]]


class BrevoClient:
    def __init__(self) -> None:
        self._api_key = settings.BREVO_API_KEY
        self._base_url = settings.BREVO_BASE_URL.rstrip("/")

    @property
    def configured(self) -> bool:
        return bool(self._api_key)

    async def upsert_contact(
        self,
        *,
        email: Optional[str],
        phone: Optional[str],
        attributes: Optional[Attrs] = None,
        list_ids: Optional[list[int]] = None,
    ) -> Optional[str]:
        """Create-or-update a Brevo contact. Returns the contact id (or
        'upserted' when Brevo returns an empty body), None on any failure."""
        if not self.configured or not (email or phone):
            return None
        body: dict = {"updateEnabled": True, "attributes": attributes or {}}
        if email:
            body["email"] = email
        if phone:
            body["sms"] = phone
        if list_ids:
            body["listIds"] = list_ids
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(
                    f"{self._base_url}/contacts",
                    headers={"api-key": self._api_key, "content-type": "application/json"},
                    json=body,
                )
            if resp.status_code in (200, 201, 204):
                data = resp.json() if resp.content else {}
                return str(data["id"]) if data.get("id") else "upserted"
            log.error("Brevo %s: %s", resp.status_code, resp.text[:200])
            return None
        except httpx.HTTPError as exc:
            log.error("Brevo transport error: %s", exc)
            return None


brevo_client = BrevoClient()
