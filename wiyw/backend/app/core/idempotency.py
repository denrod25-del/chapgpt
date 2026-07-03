"""Idempotency-Key dependency for retryable POST routes (idempotency_keys, migration 005).

Usage:
    @router.post("", status_code=201)
    async def create_lead(lead: LeadIn, idem: IdemGuard = Depends(idem_guard)) -> LeadOut:
        if idem.replay is not None:
            return LeadOut(**idem.replay)      # stored response, no side effects
        result = ...                            # normal handler body
        await idem.store(201, result.model_dump())
        return result
"""
import hashlib
import json
from dataclasses import dataclass
from typing import Any, Optional

from fastapi import HTTPException, Request

from ..db.session import get_pool


@dataclass
class IdemGuard:
    key: Optional[str]
    request_hash: Optional[str]
    endpoint: str
    replay: Optional[dict] = None       # stored response body when this is a replay

    async def store(self, status: int, body: dict) -> None:
        """Persist the response for future replays. No-op when no key was sent."""
        if not self.key:
            return
        pool = get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """UPDATE idempotency_keys
                   SET response_status=$2, response_body=$3::jsonb
                   WHERE key=$1""",
                self.key, status, json.dumps(body, default=str))


async def idem_guard(request: Request) -> IdemGuard:
    """Claim the Idempotency-Key. First caller wins; replays get the stored response;
    same key with a different body is a 422 (client bug, never silently accept)."""
    key = request.headers.get("idempotency-key")
    endpoint = request.url.path
    if not key:
        return IdemGuard(key=None, request_hash=None, endpoint=endpoint)
    if len(key) > 200:
        raise HTTPException(422, "idempotency-key too long")

    body = await request.body()         # starlette caches; Pydantic parsing re-reads the cache
    req_hash = hashlib.md5(body).hexdigest()

    pool = get_pool()
    async with pool.acquire() as conn:
        # Atomic claim: INSERT wins the race; conflict means we've seen this key.
        row = await conn.fetchrow(
            """INSERT INTO idempotency_keys (key, endpoint, request_hash)
               VALUES ($1,$2,$3)
               ON CONFLICT (key) DO NOTHING
               RETURNING key""",
            key, endpoint, req_hash)
        if row is not None:
            return IdemGuard(key=key, request_hash=req_hash, endpoint=endpoint)

        prior = await conn.fetchrow(
            "SELECT request_hash, response_status, response_body FROM idempotency_keys WHERE key=$1",
            key)
        assert prior is not None, "claimed key vanished"
        if prior["request_hash"] != req_hash:
            raise HTTPException(422, "idempotency-key reused with a different request body")
        if prior["response_body"] is None:
            # Original request still in flight (or crashed pre-store).
            raise HTTPException(409, "request with this idempotency-key is still processing")
        replay: dict[str, Any] = json.loads(prior["response_body"])
        return IdemGuard(key=key, request_hash=req_hash, endpoint=endpoint, replay=replay)
