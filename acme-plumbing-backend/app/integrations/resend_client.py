"""Resend client — transactional email transport only. Never raises; returns
explicit results so callers can log to communication_logs."""
import logging
from typing import Optional

import httpx

from app.core.config import settings

log = logging.getLogger("acme.resend")

_FROM = "Acme Plumbing <onboarding@resend.dev>"  # override once your domain is verified


class ResendClient:
    def __init__(self) -> None:
        self._api_key = settings.RESEND_API_KEY
        self._base_url = "https://api.resend.com"

    @property
    def configured(self) -> bool:
        return bool(self._api_key)

    async def send_email(
        self, *, to: str, subject: str, html: str
    ) -> tuple[bool, Optional[str]]:
        """Send one transactional email. Returns (success, external_message_id)."""
        if not (self.configured and to and subject):
            return False, None
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(
                    f"{self._base_url}/emails",
                    headers={"Authorization": f"Bearer {self._api_key}"},
                    json={"from": _FROM, "to": [to], "subject": subject, "html": html},
                )
            if resp.status_code < 300:
                data = resp.json() if resp.content else {}
                msg_id = data.get("id")
                return True, str(msg_id) if msg_id else None
            log.error("Resend %s: %s", resp.status_code, resp.text[:200])
            return False, None
        except httpx.HTTPError as exc:
            log.error("Resend transport error: %s", exc)
            return False, None


resend_client = ResendClient()
