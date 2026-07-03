# SECTION 3 — Postgres Data Model

Implemented across migrations `001`–`005` (all verified against live Postgres 16, including
005's up→down→up cycle). DDL is in `backend/migrations/`; this section is the annotated map.

## Conventions (apply to every table)

- **UUID strategy:** `UUID PRIMARY KEY DEFAULT gen_random_uuid()` (pgcrypto). Exceptions:
  append-only high-volume logs (`events`, `communication_logs`, `entity_tags`,
  `attribution_touches`) use `BIGSERIAL` — cheaper indexes, insertion-ordered, never exposed
  publicly. `tags` uses `SERIAL` (tiny lookup). The seeded WiYW brand has the **fixed UUID**
  `00000000-0000-4000-8000-000000000001` so app/n8n/seeds can reference it deterministically.
- **Timestamps:** `created_at TIMESTAMPTZ NOT NULL DEFAULT now()`; mutable tables also get
  `updated_at` maintained by the `touch_updated_at()` trigger (migration 003/005). Always
  `TIMESTAMPTZ`, always UTC in the DB; render in `brands.timezone` at the edge.
- **Soft delete:** none by default. Leads/customers are never deleted (they're the asset);
  privacy erasure = overwrite PII fields + drop Brevo mirror, keep the row for FK integrity.
  Config-ish tables (`brands`, `service_areas`, `content_pages`) use `is_active`/`status`
  flags instead of DELETE. Genuinely bad rows: hard-delete inside a transaction.
- **Idempotency keys:** `idempotency_keys` table + `Idempotency-Key` request header on
  retryable POSTs (leads/quotes/bookings/send-sms/send-email). Key = client-generated UUID.
  Replay with same key + same `request_hash` → stored response; different hash → 422.
  Webhooks dedupe separately via `webhooks_inbox (provider, dedupe_key)` unique index.
  Expiry: 48h, swept by a worker.
- **Multi-brand:** every business row carries `brand_id` (NOT NULL, defaults to WiYW's fixed
  UUID) — single-brand code paths unchanged today, `WHERE brand_id = $1` everywhere tomorrow.

## Tables

### brands (005)
One row per plumbing brand — the future SaaS tenant key.
| column | type | notes |
|---|---|---|
| id | uuid PK | fixed UUID for WiYW seed |
| slug | text UNIQUE NOT NULL | `wiyw` |
| name, website_domain, default_from_email, default_from_name | text | brand identity |
| main_phone | text | E.164 |
| booking_url, gbp_review_url | text | ⟨fill from real inputs⟩ |
| timezone | text NOT NULL default `America/New_York` | |
| is_active | boolean NOT NULL default true | soft-disable, never delete |

### service_areas (005)
Cities a brand serves; drives service-area pages + campaign geo codes. Seeded with 10 PBC
cities; Loxahatchee/The Acreage priority 10 (well water = highest ROI per KEYWORD_MAP).
Key columns: `name`, `slug`, `city_code` (short code for campaign names, e.g. `lox`),
`state`, `postal_codes text[]`, `water_profile` enum(`city|well|mixed`), `priority` (lower =
more important), `UNIQUE (brand_id, slug)`.

### leads (001)
Raw inbound demand. Statuses: `new → contacted → quoted → won|lost`.
Columns: contact fields (phone E.164 validated at boundary, email optional), `service_type`
enum (11 values incl. `water_softener`, `emergency`), `urgency` enum(`emergency|standard`),
`water_source` enum(`city|well|unknown`), UTM-ish attribution (`source`, `source_medium`,
`source_campaign`, `landing_page`), `contacted_at` (missed-lead SLA), `customer_id` FK
(set on conversion), `brevo_contact_id` (mirror pointer).
Indexes: `(status, created_at)`, `(phone)`, partial `(status, created_at) WHERE contacted_at
IS NULL` for the WF-4 missed-lead scan, `(brand_id, created_at)`.

### contacts (005 — VIEW, not a table)
Unified read model: customers ∪ unconverted leads, keyed by phone. Deliberate design:
Postgres does **not** duplicate contact rows into a third table (drift risk); "contact" is a
projection. Brevo mirrors this union.

### customers (001)
Converted contacts. `phone` UNIQUE (natural identity for a local service business),
`water_source`, `lifetime_value` + `first_job_at`/`last_job_at` (rolled by the 003 trigger on
job completion — never written by app code), `consent_sms`/`consent_email` (single source of
consent truth; unsubscribe webhooks land here). Index on `last_job_at` for the lapsed scan.

### bookings (001)
Scheduled visits. `customer_id` NOT NULL FK (CASCADE), `lead_id` FK, `scheduled_for`,
status enum `scheduled|confirmed|completed|cancelled|no_show`, `reminder_24h_sent`/
`reminder_2h_sent` booleans (WF-1 idempotency flags). Partial index on `scheduled_for WHERE
status IN ('scheduled','confirmed')` = the reminder scan.

### jobs (001)
Executed work. `booking_id` FK, `customer_id` NOT NULL FK, `completed_at`, `amount`
(NUMERIC(10,2), ≥0 CHECK), `review_requested` boolean (WF-2 idempotency flag). Completing a
job fires the LTV trigger. Partial index for the review scan.

### reviews (002 + 004)
`rating` 1–5 CHECK, `platform` enum(`google|facebook|internal`), 004 adds `author`,
`external_source` enum(`semrush|manual|gbp_direct`), `review_date`, and `dedupe_hash` with a
UNIQUE index — hash computed **in the app/n8n layer** (recipe:
`md5(platform|rating|content|YYYY-MM-DD)`, keep identical everywhere; see CLAUDE.md gotcha).

### campaigns (002) & campaign_messages (005)
`campaigns`: `name` UNIQUE following `<channel>_<purpose>_<city>_<yyyymm>`, `channel`
enum(`email|sms|social|seo`), `brevo_id` mirror pointer, start/end timestamps.
`campaign_messages`: per-step records — `channel`, `template_key`, `subject`, `position`
(UNIQUE per campaign), `send_offset_hours` (NULL = one-shot blast), `provider_template_id`.

### communication_logs (002)
Every message in/out. `channel` enum(`email|sms`), `direction` enum(`outbound|inbound`),
`to_addr`, `provider` enum(`resend|mailgun|gatewayapi|brevo`), `provider_msg_id` (indexed —
delivery webhooks update `status` by this), `template`, `status`, lead/customer FKs.

### webhooks_inbox (005)
Raw inbound webhook store — insert first, ack fast, process async. `provider` enum (8 values),
`event_type`, `dedupe_key` (provider event id or body hash; **UNIQUE per provider** — replays
become no-op inserts), `signature_valid` (nullable = provider unsigned), `headers`/`payload`
JSONB + `raw_body` text (exact bytes), `status` enum
`received|processing|processed|failed|skipped_duplicate`, `attempts`, `error`. Partial index on
pending rows for the drainer worker.

### webhook_deliveries (005)
Outbound webhook attempts (backend → n8n, future partners) with retry bookkeeping:
`target` (logical name), `url`, `event_name`, `payload`, `status`
enum(`pending|delivered|failed|dead`), `attempts`, `next_attempt_at` (partial-indexed for the
retrier), `last_status_code`, `last_error`.

### events (002, taxonomy expanded in 005)
Append-only canonical funnel log. `event_name` CHECK-enforced against the Section 9 taxonomy
(28 names), lead/customer FKs, `payload` JSONB (GIN-indexed), `source_system`
(`backend|frontend|brevo|n8n|...`). BIGSERIAL PK.

### attribution_touches (005)
Marketing touches: `touch_type` enum(`first|last|assist`), `source/medium/campaign/term/content`,
`landing_page`, `referrer`, `occurred_at`. `anonymous_id` lets the frontend record touches
before identification; CHECK requires at least one of lead/customer/anonymous id.

### tags (002) & entity_tags (002)
(The prompt's `tag_definitions` = `tags` — kept the shipped name.) `tags.name` UNIQUE,
kebab-case, 10 seeded (`lead-new`, `emergency`, `well-water`, …). `entity_tags` links tag →
lead XOR/OR customer with partial unique indexes preventing duplicate application.

### automation_runs (005)
One row per workflow execution: `workflow_key` (`wf1_appointment_reminders`), `runner`
enum(`n8n|backend|brevo`), `trigger_type`, `status` enum(`running|success|partial|failed`),
`items_in/out/failed` counters, `error`, `details` JSONB. n8n workflows open a row at start,
close it at the end — the ops dashboard for automations.

### content_pages (005)
SEO-relevant mirror of Storyblok stories: `storyblok_story_id`, `slug` (UNIQUE per brand),
`page_type` enum(`homepage|service|service_area|landing|blog|utility`), `status`
enum(`draft|published|archived`), meta title/description, `target_keyword`. Upserted by the
Storyblok publish webhook. Storyblok stays the content owner.

### seo_keyword_targets (005)
Semrush/GSC-fed rank targets: `keyword`, `city` (nullable → uniqueness via
`(brand_id, keyword, COALESCE(city,''))` index), `intent`
enum(`emergency|commercial|informational|navigational`), `target_page_id` FK → content_pages,
volume/difficulty/current_rank/best_rank, `source` enum(`semrush|gsc|manual`).

### idempotency_keys (005)
`key` (client UUID) PK, `endpoint`, `request_hash` (md5 of body), stored
`response_status`/`response_body`, `expires_at` default now()+48h (indexed for the sweeper).

## Suggested enum values (summary)

| Enum | Values |
|---|---|
| lead.status | new, contacted, quoted, won, lost |
| lead.service_type | water_treatment, water_softener, whole_house_filter, ro_system, water_heater, tankless, repipe, drain, emergency, leak, other |
| urgency | emergency, standard |
| water_source | city, well, unknown |
| booking.status | scheduled, confirmed, completed, cancelled, no_show |
| review.platform | google, facebook, internal |
| campaign.channel | email, sms, social, seo |
| comm.provider | resend, mailgun, gatewayapi, brevo |
| inbox.status | received, processing, processed, failed, skipped_duplicate |
| delivery.status | pending, delivered, failed, dead |
| run.status | running, success, partial, failed |
| page.page_type | homepage, service, service_area, landing, blog, utility |

All enums are TEXT + CHECK constraints, not Postgres ENUM types — adding a value is a
constraint swap, not a type migration.
