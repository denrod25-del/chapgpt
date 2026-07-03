# SECTION 17 — First Implementation Sprint (7 days)

Reality check: the backend, migrations 001–005, and 4 n8n workflows already exist and are
verified. The sprint is therefore **wire → harden → ship**, not greenfield. This aligns with
`plan/BUILD_ORDER.md` (the site-build track runs in parallel there; this sprint is the
backend/automation track).

## Day 1 — Environment live
- Provision Postgres (Coolify), apply migrations **001–005** in order; verify
  `SELECT * FROM tags` (10 rows) and `SELECT * FROM brands` (WiYW seeded).
- Fill `.env` boot-required keys: `DATABASE_URL`, `RESEND_API_KEY`, `GATEWAYAPI_TOKEN`,
  `OWNER_ALERT_PHONE`, `BRAND_PHONE`. Boot backend → `/health` ok.
- Smoke: `POST /leads` real payload → row + tags + events in DB (comms may still fail —
  graceful).

## Day 2 — Comms actually deliver
- Resend: verify `mail.` domain (SPF/DKIM/DMARC) → confirmation email lands in Primary.
- GatewayAPI: sender ID + credit → confirmation + owner-alert SMS arrive; register DLR webhook.
- Mailgun: `mg.` subdomain + inbound route; kill RESEND_API_KEY temporarily to prove failover.
- **End-to-end acceptance:** website form → lead → email + SMS + owner alert + DB rows.

## Day 3 — Webhook hardening (build from blueprint)
- Add `app/core/auth.py` (internal bearer) + `app/core/idempotency.py`
  (lift `scaffolds/idempotency.py`).
- Refactor webhooks to the inbox pattern (lift `scaffolds/webhooks_inbox.py`); move existing
  GatewayAPI/Resend/Brevo/Mailgun handler bodies into `_HANDLERS`. STOP-opt-out included.
- Register all provider webhook URLs (with secrets) in provider dashboards.

## Day 4 — Internal API for n8n + async comms
- Build `/api/v1/integrations/gatewayapi/send-sms`, `/resend/send-email`,
  `/brevo/sync-contact` (Section 7 skeleton) + `GET /bookings/{id}` +
  `POST /reviews/request`.
- Move `POST /leads` provider calls into `BackgroundTasks` (response waits only on Postgres).
- Mount routers under `/api/v1` (keep legacy paths during transition).

## Day 5 — Automations live
- Import n8n wf1–wf4 JSONs, remap credentials, point at prod Postgres.
- Add the `automation_runs` open/close nodes + shared error workflow (Section 12 conventions).
- Test each with seeded data: booking 23.5h out → reminder fires; completed job → review
  request; stale lead → recovery SMS.

## Day 6 — Tests + Brevo
- `tests/`: schema validation (E.164, enums, bounds), idempotency dependency (claim/replay/
  mismatch), webhook signature verification (Mailgun HMAC, Resend Svix), inbox dedupe.
  Target: the money paths, not coverage numbers.
- Brevo: domain verify, lists/segments/attributes per `docs/BREVO_SETUP.md`, `wf_welcome` +
  `wf_quote_followup` sequences; confirm backend upsert lands in `list_leads`.

## Day 7 — Deploy + verify
- Dockerize (Dockerfile shipped) → Coolify; DNS + SSL; all webhooks reachable from providers.
- Full production rehearsal: real lead from live site → complete pipeline → owner alert →
  dashboard queries return sane numbers.
- Write down what broke; file it before it's folklore.

## What to defer (deliberately NOT in the sprint)
| Deferred | Until |
|---|---|
| WF-8 escalation ladder, WF-3 inbound-C handler, WF-2b nudge | week 2 — needs live traffic to matter |
| WF-5 review monitoring (Semrush) | after Semrush project setup (BUILD_ORDER Phase 4) |
| `GET /brands/{id}/dashboard-summary` | week 2 — data first, dashboard second |
| Semrush/GSC importers, `seo_keyword_targets` population | Phase 4 |
| `webhook_deliveries` push to n8n | n8n polling works; push only if latency hurts |
| Social (LinkedIn/TikTok/X), Logo.dev | distribution phase, post-launch |
| Multi-brand routing | first paying second brand |

## Stub vs full
- **Full:** lead/quote/booking flows, webhook inbox, idempotency, wf1–wf4, Brevo sync.
- **Stub (interface + logged no-op):** Semrush/GSC clients, sitemap regen in the Storyblok
  handler (log + TODO already there), dashboard route (can return SQL-backed JSON with zeros).
- **MVP bar (end of day 2):** leads never lost, always confirmed, owner always alerted.
- **Production-hardening bar (end of day 7):** no unverified webhook processed, no double-send
  under retries, every automation observable in `automation_runs`, failover proven.
