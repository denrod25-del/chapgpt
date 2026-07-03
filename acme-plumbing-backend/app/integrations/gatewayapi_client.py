"""GatewayAPI client — SMS transport only. Never raises; returns explicit results
so callers can log to communication_logs and decide fallbacks."""
import logging
from typing import Optional

import httpx

from app.core.config import settings

log = logging.getLogger("acme.gatewayapi")


class GatewayAPIClient:
    def __init__(self) -> None:
        self._token = settings.GATEWAYAPI_API_TOKEN
        self._base_url = settings.GATEWAYAPI_BASE_URL.rstrip("/")

    @property
    def configured(self) -> bool:
        return bool(self._token)

    async def send_sms(
        self, *, to: str, message: str, sender: str = "AcmePlumb"
    ) -> tuple[bool, Optional[str]]:
        """Send one SMS. `to` must be E.164 (validated upstream).
        Returns (success, external_message_id)."""
        if not (self.configured and to and message):
            return False, None
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(
                    f"{self._base_url}/mtsms",
                    auth=(self._token, ""),
                    json={
                        "sender": sender,
                        "message": message,
                        "recipients": [{"msisdn": int(to.lstrip("+"))}],
                    },
                )
            if resp.status_code < 300:
                ids = resp.json().get("ids") or []
                return True, str(ids[0]) if ids else None
            log.error("GatewayAPI %s: %s", resp.status_code, resp.text[:200])
            return False, None
        except (httpx.HTTPError, ValueError) as exc:
            log.error("GatewayAPI transport error: %s", exc)
            return False, None


gatewayapi_client = GatewayAPIClient()
