# SECTION 1 — Architecture Overview

## System boundaries

```
                    ┌────────────────────────────── CONTENT ─────────────────────────────┐
                    │  Storyblok (CMS)  →  Next.js site (whatsinyourwater.com)           │
                    └───────────────┬────────────────────────────────────────────────────┘
                                    │ POST /leads /quotes /events (public, rate-limited)
                                    ▼
┌──────────────── CORE (you own) ─────────────────────────────────────────────────────────┐
│  FastAPI backend ──── Postgres (SYSTEM OF RECORD) ──── n8n (scheduled/delayed automation)│
│      ▲ webhooks_inbox                                        │                           │
└──────┼───────────────────────────────────────────────────────┼──────────────────────────┘
       │ provider webhooks (signed)                            │ REST calls
       ▼                                                       ▼
┌─────────────── COMMS (rented) ──────────────┐   ┌────────── SEO/ANALYTICS (read-mostly) ─┐
│ Brevo      marketing email, lists, nurture  │   │ Semrush   rank, listings, review watch │
│ Resend     transactional email (primary)    │   │ GSC       index status, queries        │
│ Mailgun    transactional failover + inbound │   │ Logo.dev  brand asset lookups          │
│ GatewayAPI all SMS                          │   │ LinkedIn/TikTok/X  distribution only   │
└─────────────────────────────────────────────┘   └────────────────────────────────────────┘
```

Boundary rules: the frontend never talks to providers directly — everything goes through the
backend. Providers never write to Postgres directly — only via signed webhooks into
`webhooks_inbox`. n8n reads/writes Postgres and calls providers, but never bypasses the
ownership rules below.

## Source of truth (per docs/OWNERSHIP.md — canonical)

| Domain | Owner | Notes |
|--------|-------|-------|
| **Contacts** (leads + customers) | **Postgres** | Brevo is a *mirror* for marketing. `contacts` view = customers ∪ unconverted leads |
| **Campaigns** | **Postgres** (`campaigns`, `campaign_messages`) for the record; **Brevo** executes email sequences | Campaign *results* flow back as events |
| **Jobs / bookings** | **Postgres** (`bookings`, `jobs`) | LTV rolls up via DB trigger (migration 003) |
| **Communication logs** | **Postgres** (`communication_logs`) | Every outbound message logged with provider msg id; delivery webhooks update status |
| **Analytics / events** | **Postgres** (`events`) | Canonical funnel log. GSC/Semrush imported later into `seo_keyword_targets`, never authoritative for leads |
| **Content** | **Storyblok** | `content_pages` mirrors SEO-relevant metadata only |
| **Reviews** | **Postgres** (`reviews`) | Semrush monitors GBP and feeds it (WF-5); GBP is the public surface |

## Email/SMS provider responsibility (default, justified)

- **Brevo** — marketing only: lists, segments, nurture/drip sequences, reactivation campaigns.
  *Why:* it's the only tool in the stack with segment/automation primitives; keeping campaigns
  in one place protects the transactional domain's deliverability reputation.
- **Resend** — transactional primary: lead/booking confirmations, owner notices, review-request
  email leg. *Why:* simplest API, excellent deliverability on a dedicated subdomain
  (`mail.whatsinyourwater.com`).
- **Mailgun** — transactional **failover** (on Resend non-2xx only) + inbound email parse
  (`mg.` subdomain). *Why:* second provider = no single point of failure for
  money-path messages; Mailgun's inbound routing is mature.
- **GatewayAPI** — every SMS (confirmations, reminders, review requests, owner alerts, emergency
  acknowledgements). One SMS provider = one opt-out list, one sender identity, one DLR pipeline.

Never cross: no campaign from Resend/Mailgun; no receipt from Brevo. (See Section 11 for the
full decision table.)

## CMS vs backend division

| Concern | Storyblok (CMS) | FastAPI backend |
|---------|-----------------|-----------------|
| Pages, copy, images, wireframed blocks | ✅ owns | reads nothing |
| Form **rendering** | ✅ (contact_form block) | — |
| Form **submission** | posts to backend | ✅ validates (Pydantic), persists, triggers comms |
| Publish lifecycle | fires webhook | ✅ `/webhooks/storyblok` → sitemap rebuild + GSC ping + `content_pages` upsert |
| SEO metadata | authored in Storyblok | mirrored to `content_pages` for rank joins |
| Anything with PII | ❌ never | ✅ always |

## Event-driven architecture summary

1. **Ingest** — frontend posts funnel events to `POST /events`; forms post to `/leads`//`quotes`;
   providers post signed webhooks. All webhook payloads land raw in `webhooks_inbox` *before*
   processing (dedupe on `(provider, dedupe_key)`), endpoint returns 200 immediately, a
   background task processes the row.
2. **Canonical log** — every meaningful state change appends to `events` (CHECK-enforced
   taxonomy, Section 9). The `events` table is append-only; consumers never mutate it.
3. **React** — two reaction tiers:
   - **Synchronous (FastAPI, in-request):** new-lead confirmation + owner alert + emergency
     fast-response. These must fire in seconds; they live in `POST /leads`, not n8n.
   - **Scheduled/delayed (n8n):** reminders, review requests, reactivation, missed-lead
     recovery — poll Postgres on cron, act, write results back (comm logs, tags, events,
     `automation_runs`).
4. **Mirror** — contact changes upsert into Brevo (one-way). Brevo/provider engagement webhooks
   flow back as events + consent updates only.
5. **Measure** — dashboard reads aggregate `events` + `communication_logs` + `automation_runs`;
   attribution reads `attribution_touches`.

**Double-send guard (critical):** every automation has exactly one home. New-lead and emergency
flows run in FastAPI; do not also build them live in n8n. Review-request legs are split
SMS=GatewayAPI / initial email=Resend / delayed nurture=Brevo — each system fires exactly one leg.
