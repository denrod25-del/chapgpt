# SECTION 7 — FastAPI Code Scaffold

**ORM decision:** the shipped backend uses **raw asyncpg + a repository layer**, not
SQLAlchemy/SQLModel. This is deliberate and stays: parameterized SQL only (NASA-light rule),
zero ORM magic, and the n8n workflows speak the same SQL dialect against the same tables.
Consistency with boot-tested code beats re-platforming.

## Already shipped — read these, don't regenerate

| Concern | File | Pattern shown |
|---|---|---|
| Entrypoint + lifespan + router registration | `app/main.py` | `asynccontextmanager` lifespan: `config.validate()` fail-fast → `init_pool()` |
| Settings/config | `app/config.py` | env-read class + `_REQUIRED` boot assertion |
| DB session/pool | `app/models/db.py` | module-level asyncpg pool, bounded (2–10), `get_pool()` accessor |
| Repository layer | `app/models/repo.py` | all SQL parameterized; `upsert_lead`, `emit_event`, `add_tag`, `log_comm` |
| Lead creation endpoint | `app/routers/leads.py` | txn for DB writes → comms **outside** the txn → comm-log write-back |
| Webhook receivers (current form) | `app/routers/webhooks.py`, `quotes_reviews.py` | HMAC verification (Mailgun, Storyblok) |
| Service layer (business flows) | `app/services/email.py` | Resend→Mailgun failover; never raises, returns bool |
| Brevo integration client | `app/services/brevo.py` | upsert contact, never raises, logs failures |
| GatewayAPI integration client | `app/services/sms.py` | returns `(ok, provider_msg_id)`; SMS copy templates |

## New scaffolds (in `scaffolds/`, liftable as-is)

| File | Provides |
|---|---|
| [`scaffolds/idempotency.py`](scaffolds/idempotency.py) | `Idempotency-Key` dependency: atomic claim via `INSERT … ON CONFLICT DO NOTHING`, replay returns stored response, hash-mismatch → 422, in-flight → 409 |
| [`scaffolds/webhooks_inbox.py`](scaffolds/webhooks_inbox.py) | Full inbox pattern: verify → store raw (deduped) → 200 fast → `BackgroundTasks` processing with status-claim so a drainer worker can coexist; Brevo + GatewayAPI processors incl. STOP handling |

Both require migration 005. Wire them in when refactoring webhooks to the inbox pattern
(sprint day 3, Section 17) — the current inline handlers keep working until then.

## Remaining skeletons

### Internal auth dependency (`app/core/auth.py`)

```python
import hmac
from fastapi import Header, HTTPException
from ..config import config

async def require_internal(authorization: str = Header(default="")) -> None:
    """Bearer guard for n8n/admin routes. Constant-time compare."""
    expected = f"Bearer {config.INTERNAL_API_TOKEN}"
    if not (config.INTERNAL_API_TOKEN and hmac.compare_digest(authorization, expected)):
        raise HTTPException(401, "missing or invalid internal token")

# usage: router = APIRouter(prefix="/integrations", dependencies=[Depends(require_internal)])
```

### Background task pattern (rule of thumb)

- **In-request `BackgroundTasks`** — anything the caller shouldn't wait for but that has its
  own durability (inbox rows, comm logs): webhook processing, Brevo mirror sync.
- **DB-backed queue + cron drainer** — anything that must survive a process crash:
  `webhooks_inbox` rows in `received/failed` (drainer re-runs `process_inbox_row`),
  `webhook_deliveries` retries, `idempotency_keys` sweep. Drainer = n8n schedule hitting an
  internal endpoint, or a `workers/` loop — n8n is already the scheduler; use it first.
- **Never** `asyncio.create_task` fire-and-forget for anything with side effects.

Refactor note: `POST /leads` currently awaits provider calls in-request (boot-tested, fine at
launch volume). Sprint day 4 moves comms to `BackgroundTasks` after the txn commits — the
201 response then only waits for Postgres.

### Send-SMS internal route (`app/routers/integrations.py`)

```python
from fastapi import APIRouter, Depends
from ..core.auth import require_internal
from ..core.idempotency import IdemGuard, idem_guard
from ..models.db import get_pool
from ..models import repo
from ..services import sms
from ..schemas.integrations import SmsSend, SmsSendOut

router = APIRouter(prefix="/integrations", tags=["integrations"],
                   dependencies=[Depends(require_internal)])


@router.post("/gatewayapi/send-sms", response_model=SmsSendOut)
async def send_sms(body: SmsSend, idem: IdemGuard = Depends(idem_guard)) -> SmsSendOut:
    if idem.replay is not None:
        return SmsSendOut(**idem.replay)
    ok, msg_id = await sms.send_sms(body.to, body.message)
    pool = get_pool()
    async with pool.acquire() as conn:
        await repo.log_comm(conn, channel="sms", direction="outbound", to_addr=body.to,
                            provider="gatewayapi", template=body.template,
                            status="sent" if ok else "failed",
                            provider_msg_id=msg_id, lead_id=body.lead_id)
    out = SmsSendOut(sent=ok, provider_msg_id=msg_id)
    await idem.store(200, out.model_dump())
    return out
```

The Brevo sync-contact and send-email routes follow the identical shape over
`services/brevo.upsert_contact` and `services/email` — thin handler, service does the work,
comm log written, idempotency stored.

### Config additions (`app/config.py`)

Add to the existing class (same style):
```python
INTERNAL_API_TOKEN = os.environ.get("INTERNAL_API_TOKEN", "")
BREVO_WEBHOOK_TOKEN = os.environ.get("BREVO_WEBHOOK_TOKEN", "")
GATEWAYAPI_WEBHOOK_SECRET = os.environ.get("GATEWAYAPI_WEBHOOK_SECRET", "")
RESEND_WEBHOOK_SECRET = os.environ.get("RESEND_WEBHOOK_SECRET", "")
CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "")
BREVO_LIST_NEW_LEADS = int(os.environ.get("BREVO_LIST_NEW_LEADS", "2"))
BREVO_LIST_CUSTOMERS = int(os.environ.get("BREVO_LIST_CUSTOMERS", "3"))
```
(`services/brevo.py` currently hardcodes `listIds: [2]` — switch it to
`config.BREVO_LIST_NEW_LEADS` when touching that file.)
