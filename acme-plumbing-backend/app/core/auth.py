"""Internal bearer auth for machine-to-machine routes (n8n, admin scripts)."""
import hmac

from fastapi import Header, HTTPException

from app.core.config import settings


async def require_internal(authorization: str = Header(default="")) -> None:
    """401 unless the caller presents `Authorization: Bearer <INTERNAL_API_TOKEN>`.
    An unset token denies everything — internal routes are never open by accident.
    n8n sends this header on every /integrations/* and /reviews/request call."""
    expected = f"Bearer {settings.INTERNAL_API_TOKEN}"
    if not (settings.INTERNAL_API_TOKEN and hmac.compare_digest(authorization, expected)):
        raise HTTPException(status_code=401, detail="missing or invalid internal token")
