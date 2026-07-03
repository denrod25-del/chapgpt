"""Internal bearer auth for n8n/admin routes. Constant-time compare."""
import hmac

from fastapi import Header, HTTPException

from .config import config


async def require_internal(authorization: str = Header(default="")) -> None:
    """401 unless the caller presents Bearer INTERNAL_API_TOKEN.
    An unset token denies everything — internal routes are never open by accident."""
    expected = f"Bearer {config.INTERNAL_API_TOKEN}"
    if not (config.INTERNAL_API_TOKEN and hmac.compare_digest(authorization, expected)):
        raise HTTPException(401, "missing or invalid internal token")
