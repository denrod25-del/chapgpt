# CLAUDE.md — What's in Your Water (WiYW)

Context for Claude Code working in this repo. Read this first.

## What this is
Marketing + operations system for **What's in Your Water (WiYW)** — a Palm Beach County, FL
business doing **water treatment + full plumbing**. The system captures leads, confirms and
reminds bookings, requests reviews, reactivates old customers, and drives local SEO. Built to be
productized into a repeatable SaaS for other plumbing companies later, so keep things portable.

## Architecture (one line)
Storyblok (content) → Next.js site → FastAPI backend (`/leads`, `/events`, webhooks) → Postgres
(system of record) → n8n (scheduled automations) → Brevo/Resend/GatewayAPI (comms) + Semrush/GSC (SEO).

## System ownership — DO NOT violate (see docs/OWNERSHIP.md)
- **Postgres** = system of record for all leads/customers/bookings/jobs/reviews. Everything mirrors from here.
- **Brevo** = marketing email only (campaigns, segments, nurture). NEVER transactional receipts.
- **Resend** = transactional email (confirmations, notices). **Mailgun** = failover + inbound parse.
- **GatewayAPI** = all SMS (confirmations, reminders, review requests, owner alerts).
- **Semrush** = local SEO ops (rank, listings, review monitoring, on-page). Sends no mail, stores no contacts.
- **Storyblok** = content/pages.
Rule of thumb: campaign/list/sequence → Brevo. 1:1 system message → Resend. Never cross these.

## Code standards (NASA-light — apply to all backend work)
Derived from JPL/NPR 7150.2D/Power of Ten. On every change:
- Validate inputs at boundaries (Pydantic does this; keep it).
- Check return values; no silent exception swallowing (log failures explicitly).
- Bounded loops; smallest scope; short functions (~60 lines).
- Assertions on invariants. Parameterized SQL only — never string-interpolate queries.
State the tier in one line before non-trivial changes: Strict (money/safety/data-critical),
NASA-light (default), Pragma (throwaway).

## Repo layout
```
backend/     FastAPI + Postgres. BOOT-TESTED. Canonical. Start here.
  app/       api/v1/ core/ db/ models/ schemas/ services/ integrations/ webhooks/ + main.py
  migrations/ 001-005 apply in order. down.sql reverses each.
n8n/         4 importable workflow JSONs + WORKFLOWS.md + WF5 spec (review monitoring)
storyblok/   React components + tokens.css + component-schemas.json + preview-homepage.html
docs/        OWNERSHIP, BREVO_SETUP, KEYWORD_MAP, 3 wireframe sets (12 pages)
  blueprint/ 17-section backend/automation handoff blueprint + liftable scaffolds
plan/        BUILD_ORDER.md — sequenced task list
```

## What's verified vs what's not
VERIFIED (tested this session):
- Migrations 001–004 apply on live Postgres; LTV trigger + event-taxonomy CHECK + review dedup all work.
- Migration 005 (brands/service_areas/webhooks_inbox/idempotency/expanded taxonomy) applies clean,
  survives an up→down→up cycle, inbox dedupe rejects duplicates, and the booted backend still
  passes /leads + /events smoke tests against the 005 schema (brand_id auto-fills).
- Backend boots; `/leads`, `/events`, `/quotes`, `/reviews`, `/health` respond; E.164 + rating bounds reject bad input; well-water auto-tag works. Comms fail gracefully with bad keys.
- All 4 n8n JSONs parse; connections reference real nodes.
- Storyblok components typecheck clean.
NOT yet done (your job):
- Next.js app shell that mounts the Storyblok components (components exist; the app that renders them doesn't).
- Wiring live API keys (Resend/GatewayAPI/Brevo/Storyblok/Semrush) into env.
- Building the 12 pages in Storyblok from the wireframes + schemas.
- Deploying (Coolify/Docker target). Remaining 3 n8n workflows exist as JSON; WF-5 is spec-only (needs building).

## Gotchas discovered this session
- `pgcrypto` must be enabled for `gen_random_uuid()` — standard Postgres has it; keep the `CREATE EXTENSION` line.
- Review dedup hash is computed in the app/n8n layer, NOT a generated column (Postgres rejects non-IMMUTABLE generated expressions). Keep the hash recipe identical between the WF-5 upsert and the migration-004 backfill.
- asyncpg wants a standard TCP DSN (`postgresql://user:pass@host:5432/wiyw`). Don't use socket query-string DSNs.
- Storyblok CSS currently lives in preview-homepage.html as the reference implementation — port it into the Next.js global stylesheet when building the app.

## Business facts that drive content (verified June 2026)
- PBC water: 15–22 GPG (Biscayne Aquifer) — needs 48k-grain softeners, not the national 32k default.
- Pricing: city softener $1,200–$2,800; well+iron pre-treatment $3,500–$6,500; filtration from $2,500.
- PFAS: 4 ppt MCL for PFOA/PFOS intact for **public systems**, compliance timeline to 2031. Private wells excluded entirely — WiYW's western-PBC well-water differentiator.
- Highest-ROI SEO: well-water pages for Loxahatchee/The Acreage/Wellington (thin competition, high ticket).

## Start here
Read `plan/BUILD_ORDER.md` for the sequenced task list, then `README.md` for setup commands.
