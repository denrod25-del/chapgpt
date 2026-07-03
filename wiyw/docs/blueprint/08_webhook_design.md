# SECTION 8 — Webhook Design

Universal pipeline (implemented in [`scaffolds/webhooks_inbox.py`](scaffolds/webhooks_inbox.py)):

```
verify signature → INSERT raw into webhooks_inbox (deduped) → return 200 (<50ms)
                                                            → BackgroundTask processes the row
failed rows (attempts<5) re-claimed by a scheduled drainer; bad-signature rows stored
with status=failed for forensics but NEVER processed.
```

Principles: the endpoint does no business work; a webhook is *evidence*, the inbox row is the
durable record; duplicates die at the unique index, not in handler logic; we return 200 even on
bad payloads (provider retry storms help nobody — alerting keys off failed-row counts).

## Per-provider matrix

| | Brevo | Mailgun | GatewayAPI | Resend | Storyblok | Forms (future) | Internal |
|---|---|---|---|---|---|---|---|
| **Path** | `/api/v1/webhooks/brevo` | `/webhooks/mailgun` | `/webhooks/gatewayapi` | `/webhooks/resend` | `/webhooks/storyblok` | `/webhooks/forms` | `/webhooks/internal` |
| **Events** | opened, click, delivered, unsubscribe, hard_bounce | delivered, failed, complained + inbound parse | SMS DLR (DELIVERED/UNDELIVERABLE), inbound MO (STOP) | email.delivered/.opened/.clicked/.bounced | story published/unpublished | vendor form submission | backend→n8n handoffs |
| **Signature** | none native → require `?token=$BREVO_WEBHOOK_TOKEN` in the URL, constant-time compare | HMAC-SHA256 of `timestamp+token` with signing key (✅ shipped) | none native → secret URL path segment `$GATEWAYAPI_WEBHOOK_SECRET` + source-IP allowlist optional | Svix headers: HMAC-SHA256 of `{id}.{timestamp}.{body}` with `RESEND_WEBHOOK_SECRET` | HMAC-SHA1 of raw body with `STORYBLOK_WEBHOOK_SECRET` (✅ shipped) | per-vendor; else shared token | `INTERNAL_API_TOKEN` bearer |
| **Dedupe key** | payload `id` (fallback: md5 of raw body) | `signature.token` (unique per delivery) | `{id}:{status}` (one DLR per state) | Svix `svix-id` header | `{story_id}:{action}:{published_at}` | vendor event id, else body hash | caller-supplied `event_id` |
| **Timestamp check** | — | reject if `abs(now - timestamp) > 300s` (replay guard) | — | reject if svix-timestamp drift > 300s | — | — | — |

## Retry handling

- **Provider side:** all listed providers retry on non-2xx with backoff. We therefore return
  2xx for everything except infrastructure failure (DB down → 500 is correct: the retry will
  succeed later and the unique index absorbs any overlap).
- **Our side:** rows in `received`/`failed` with `attempts < 5` are re-claimed by the drainer
  (n8n schedule, every 5 min: `POST /api/v1/internal/drain-inbox` or direct
  `process_inbox_row` loop). After 5 attempts the row stays `failed` and surfaces in
  observability. The status-flip claim (`UPDATE … WHERE status IN (…) RETURNING`) makes
  inline task + drainer race-safe.

## Processing flows (async, per provider)

- **Brevo** → map opened/click/delivered → `email_*` events; unsubscribe →
  `customers.consent_email=false` + `contact_unsubscribed` event. Hard bounce → mark comm log,
  flag contact.
- **Mailgun** → delivery events update `communication_logs.status` by `provider_msg_id`;
  inbound parse (reply emails) → `communication_logs` row `direction=inbound` + owner-alert
  email via Resend.
- **GatewayAPI** → DLR updates comm-log status + `sms_delivered` event; inbound `STOP` →
  `consent_sms=false` + `contact_unsubscribed` (implemented in the scaffold).
- **Resend** → update comm-log status; bounces flag the address (stop the Mailgun failover
  from retrying a dead mailbox).
- **Storyblok** → upsert `content_pages` from story metadata; regenerate sitemap; ping GSC.
- **Forms** → normalize vendor payload → construct `LeadIn` → run the same lead flow as
  `POST /leads` (share the service function, don't re-implement).
- **Internal** → reserved for future backend→n8n event pushes via `webhook_deliveries`
  (today n8n polls Postgres; keep polling until latency demands push).

## Observability fields (log on every webhook, JSON)

`provider, event_type, inbox_id, dedupe_key, signature_valid, duplicate, processing_ms,
status, error`. Metrics worth a weekly look: inbox rows by `status` per provider (alert on
`failed > 0` older than 1h), p95 ack latency, duplicate rate (sudden spike = provider incident
or a replay attack).

## Migration note

Shipped handlers (`routers/webhooks.py`, `quotes_reviews.py`) verify signatures but process
inline and don't store raw payloads. They work; refactor to the inbox pattern on sprint day 3
by moving their processing bodies into `_HANDLERS` processors — endpoint paths and provider
config don't change.
