# SECTION 2 — Repository Structure

Current structure (built, boot-tested) and target structure as the app grows. Don't reshuffle
working code to match the target early — move a module when it earns it (≥2 files of the same
kind).

## Current (canonical)

```
wiyw/
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI entrypoint, lifespan (pool init), router registration
│   │   ├── config.py          # env config, fail-fast validation at boot
│   │   ├── routers/           # HTTP layer — thin handlers only
│   │   │   ├── leads.py       #   POST /leads (new-lead + emergency automations inline)
│   │   │   ├── bookings.py    #   /bookings + /jobs
│   │   │   ├── quotes_reviews.py  # /quotes, /reviews + Mailgun/Brevo webhooks
│   │   │   ├── events.py      #   POST /events (frontend funnel ingestion)
│   │   │   ├── webhooks.py    #   /webhooks/{gatewayapi,resend,storyblok}
│   │   │   └── schemas_ext.py #   booking/job/quote/review Pydantic models
│   │   ├── models/
│   │   │   ├── db.py          # asyncpg pool (init/close/get)
│   │   │   ├── repo.py        # repository layer — ALL SQL lives here, parameterized
│   │   │   └── schemas.py     # core Pydantic models (LeadIn/LeadOut/EventIn) + enums
│   │   └── services/          # provider clients + business flows
│   │       ├── email.py       #   Resend primary → Mailgun failover
│   │       ├── sms.py         #   GatewayAPI + message templates
│   │       └── brevo.py       #   contact mirror upsert
│   ├── migrations/            # 001–005 numbered SQL, each with .down.sql rollback
│   ├── schema.sql             # readable reference (migrations are the source of truth)
│   ├── Dockerfile  requirements.txt  .env.example
├── n8n/                       # importable workflow JSONs + WORKFLOWS.md specs
├── storyblok/                 # React components, tokens.css, block schemas, preview html
├── docs/                      # OWNERSHIP, BREVO_SETUP, KEYWORD_MAP, wireframes, blueprint/
└── plan/                      # BUILD_ORDER.md
```

## Target structure (grow into as modules earn it)

| Folder | Purpose | When to create |
|--------|---------|----------------|
| `app/api/` | Versioned route packages (`api/v1/`) once `/api/v1` prefix lands; `routers/` modules move under it unchanged | when adding the v1 prefix (Section 6) |
| `app/models/` | DB access: pool, repositories. Stays raw-asyncpg (deliberate — see Section 7) | exists |
| `app/schemas/` | Split Pydantic models out of `models/schemas.py` + `routers/schemas_ext.py` into per-domain files (`leads.py`, `bookings.py`, `webhooks.py`) | when a third schema file appears |
| `app/services/` | Business flows that orchestrate repos + integrations (e.g. `lead_flow.py` extracted from the router) | when a second consumer of the flow appears (n8n-triggered variant) |
| `app/integrations/` | Pure provider clients (Brevo, GatewayAPI, Resend, Mailgun, Semrush, GSC) — no business logic, no DB | when Semrush/GSC importers land |
| `app/webhooks/` | Inbound webhook receivers + `webhooks_inbox` processing (Section 8 pattern) | with the inbox refactor |
| `app/workers/` | Background processors: inbox drainer, webhook_deliveries retrier, idempotency-key sweeper | with the inbox refactor |
| `app/core/` | Cross-cutting: config, logging setup, auth dependencies, idempotency dependency | when `config.py` gets siblings |
| `tests/` | pytest: schema validation, repo layer against a disposable PG, webhook signature verification | Sprint day 6 (Section 17) |
| `migrations/` | Numbered forward + `.down.sql` pairs, applied in order | exists |
| `docs/` | This blueprint + ownership + setup docs | exists |

Rules that hold at any size:
- Route handlers stay thin; SQL only in `models/repo*.py`; provider HTTP only in
  `services/`/`integrations/`.
- Every migration has a tested `.down.sql`.
- `schemas_ext.py` naming is legacy — fold into `app/schemas/` at the v1 refactor, don't add a
  third "ext" file.
