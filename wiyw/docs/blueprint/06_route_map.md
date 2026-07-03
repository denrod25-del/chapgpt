# SECTION 6 — FastAPI Route Map

**Versioning decision:** shipped routes are unprefixed (`/leads`, `/webhooks/...`). Target
contract is `/api/v1/*`. Migration path: mount every existing router twice during transition —
`app.include_router(r)` **and** `app.include_router(r, prefix="/api/v1")` — flip the frontend
to `/api/v1`, then drop the legacy mount. Zero handler changes.

**Auth tiers**
- `public` — website traffic; per-IP rate limited; no credentials.
- `internal` — `Authorization: Bearer $INTERNAL_API_TOKEN` (n8n, admin scripts).
- `signed` — provider webhook; HMAC/signature verification per Section 8; no bearer token.

| Route | Auth | Status | Purpose |
|---|---|---|---|
| `POST /api/v1/leads` | public | ✅ shipped (`/leads`) | Lead intake; runs new-lead + emergency automations |
| `POST /api/v1/quote-requests` | public | ✅ shipped as `/quotes` (keep that name) | High-intent quote request |
| `POST /api/v1/bookings` | internal | ✅ shipped | Create booking + confirmation comms |
| `GET /api/v1/bookings/{id}` | internal | ➕ build (trivial SELECT) | Fetch booking + status |
| `POST /api/v1/reviews/request` | internal | ➕ build | Trigger split-leg review flow for a job |
| `POST /api/v1/events` | public | ✅ shipped | Frontend funnel event ingestion |
| `POST /api/v1/webhooks/brevo` | signed | ✅ shipped → refactor to inbox pattern | Opens/clicks/unsubs |
| `POST /api/v1/webhooks/mailgun` | signed | ✅ shipped (HMAC verified) → inbox | Delivery events + inbound parse |
| `POST /api/v1/webhooks/gatewayapi` | signed | ✅ shipped → inbox + STOP handling | SMS DLRs, inbound STOP |
| `POST /api/v1/webhooks/forms` | signed | ➕ build only if a 3rd-party form tool is adopted | External form vendors → lead |
| `POST /api/v1/webhooks/resend` | signed | ✅ shipped (bonus, keep) | Resend delivery events |
| `POST /api/v1/webhooks/storyblok` | signed | ✅ shipped (sitemap regen TODO) | Publish → sitemap + GSC ping + content_pages upsert |
| `POST /api/v1/integrations/brevo/sync-contact` | internal | ➕ build (thin wrapper over `services/brevo.py`) | Manual/n8n-driven contact mirror |
| `POST /api/v1/integrations/gatewayapi/send-sms` | internal | ➕ build (wrapper over `services/sms.py` + comm log) | n8n sends SMS through backend, one logging path |
| `POST /api/v1/integrations/resend/send-email` | internal | ➕ build (wrapper over `services/email.py`) | Same for email; failover built in |
| `POST /api/v1/integrations/mailgun/send-email` | internal | ⛔ skip | Mailgun is automatic failover inside the email service — a separate route invites ownership violations |
| `GET /api/v1/health` | public | ✅ shipped (`/health`) | Liveness + brand |
| `GET /api/v1/brands/{brand_id}/dashboard-summary` | internal | ➕ build | Aggregate KPIs |

## Per-route contracts (new/changed routes; shipped ones documented in code)

### GET /api/v1/bookings/{id}
Response `200 {id, customer_id, lead_id, scheduled_for, service_type, status,
reminder_24h_sent, reminder_2h_sent, created_at}`. Errors: 404, 401. No side effects.

### POST /api/v1/reviews/request
Request: `ReviewRequestPayload` (Section 5). Side effects: mark `jobs.review_requested=true`,
send SMS leg (consent-gated) or email leg, insert comm log, tag `review-requested`, emit
`review_request_sent`. Idempotency: guarded by `review_requested` flag — a replay is a 409
(`already_requested`). Errors: 404 job, 409 already requested, 422 validation.
**Overlap warning:** WF-2 (n8n) auto-requests reviews on a schedule. This route is the manual/
immediate trigger; both paths share the same `review_requested` flag so they can't double-send.

### POST /api/v1/integrations/gatewayapi/send-sms
Request: `SmsSend`. Response: `SmsSendOut`. Side effects: GatewayAPI call + comm-log row.
Idempotency: `Idempotency-Key` header honored (Section 3 strategy). Errors: 401, 422, 502
(provider down — n8n retries). Rationale for existing: n8n *can* call GatewayAPI directly
(current WF JSONs do); routing through the backend gives one comm-log/consent/opt-out path.
Recommended default: **new workflows use this route; migrate WF-1/2/4 when touched.**

### POST /api/v1/integrations/resend/send-email
Request: `EmailSend`. Calls `services/email.send(...)` — Resend primary, Mailgun failover
automatically; response reports which provider won. Same auth/idempotency as send-sms.

### POST /api/v1/integrations/brevo/sync-contact
Request: `BrevoContactSync`. Response: `{contact_id}`. Side effect: Brevo upsert +
`leads.brevo_contact_id` update when resolvable. Idempotent by nature (upsert).

### GET /api/v1/brands/{brand_id}/dashboard-summary
Response:
```json
{
  "brand_id": "…", "window_days": 30,
  "leads": {"total": 42, "emergency": 6, "by_source": {"website": 30, "gbp": 12}},
  "conversion": {"lead_to_booking": 0.38, "booking_to_completed": 0.85},
  "revenue": {"completed_jobs": 19, "total_amount": 41250.00},
  "reviews": {"requested": 15, "received": 7, "avg_rating": 4.9},
  "comms": {"sms_sent": 120, "email_sent": 85, "delivery_rate": 0.97},
  "automations": {"runs": 96, "failed": 1}
}
```
Read-only aggregates over `leads/bookings/jobs/reviews/communication_logs/automation_runs`
filtered by `brand_id`. Cache 60s in-process. Errors: 401, 404 brand.

## Cross-cutting idempotency rules

| Route class | Mechanism |
|---|---|
| Public POSTs (leads, quote-requests, events) | `Idempotency-Key` header (frontend generates UUID per submission attempt); duplicate submissions without a key are acceptable business-wise (a dup lead is mergeable, a lost lead is not) |
| Internal sends (sms/email) | `Idempotency-Key` required — n8n retry policies will replay |
| Webhooks | never idempotency-keyed; deduped by `webhooks_inbox (provider, dedupe_key)` |
| Bookings/reviews/request | natural guards (`review_requested`, reminder flags) + `Idempotency-Key` |
