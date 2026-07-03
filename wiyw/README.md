# What's in Your Water (WiYW) — Marketing & Ops System

Complete, handoff-ready system for a Palm Beach County water-treatment + plumbing business.
Lead capture → booking confirmation → reminders → review requests → reactivation → local SEO.

> **Working with Claude Code?** Read `CLAUDE.md` first — it has the ownership rules, code
> standards, verified-vs-unverified status, and gotchas. Then `plan/BUILD_ORDER.md` for sequencing.

## Structure
```
wiyw/
├── CLAUDE.md              ← project context for Claude Code (read first)
├── README.md             ← this file
├── backend/              ← FastAPI + Postgres (boot-tested, canonical)
│   ├── app/              routers, services, models, main.py, config.py
│   ├── migrations/       001–005 (+ rollbacks), apply in order
│   ├── schema.sql        full schema (reference; migrations are the source of truth)
│   ├── requirements.txt  Dockerfile  .env.example  MERGE_NOTES.md
├── n8n/                  ← 4 workflow JSONs (importable) + WORKFLOWS.md + WF5 spec
├── storyblok/           ← React components, tokens.css, block schemas, homepage preview
├── docs/                ← OWNERSHIP, BREVO_SETUP, KEYWORD_MAP, 3 wireframe sets (12 pages)
│   └── blueprint/       ← 17-section backend/automation handoff blueprint + scaffolds
└── plan/                ← BUILD_ORDER.md (sequenced task list)
```

## Quick start — backend
```bash
cd backend
createdb wiyw
psql wiyw -f migrations/001_core_entities.sql
psql wiyw -f migrations/002_marketing_entities.sql
psql wiyw -f migrations/003_triggers.sql
psql wiyw -f migrations/004_reviews_dedup.sql
psql wiyw -f migrations/005_platform_entities.sql
cp .env.example .env         # fill in real keys
pip install -r requirements.txt
uvicorn app.main:app --reload
# GET http://localhost:8000/health  -> {"status":"ok","brand":"What's in Your Water"}
```

## Quick start — Storyblok/frontend
The components exist; the Next.js app that mounts them does not yet (that's a build task).
See `storyblok/README.md`. Open `storyblok/preview-homepage.html` in a browser to see the design.

## Quick start — n8n
Import the 4 JSONs in `n8n/` (n8n → Import from File), remap the `REPLACE_*` credential
placeholders. WF-5 (review monitoring) is a spec in `n8n/WF5_review_monitoring.md` — build it
from the node-by-node doc.

## Endpoints (backend)
- `POST /leads` — website lead intake (runs new-lead + emergency flows synchronously)
- `POST /quotes` — quote request (high-intent lead + follow-up)
- `POST /bookings`, `PATCH /bookings/{id}` — booking + status
- `POST /jobs`, `PATCH /jobs/{id}/complete` — job lifecycle (completion rolls customer LTV)
- `POST /reviews` — internal review capture
- `POST /events` — frontend event ingestion (call_clicked, page views)
- `POST /webhooks/{gatewayapi|resend|mailgun|storyblok|brevo}` — provider callbacks
- `GET /health`

## The 12 pages (wireframed in docs/, build in Storyblok)
Phase 1: homepage, emergency, water softener, well water treatment, whole-house filtration, water heater.
Phase 2: reverse osmosis, drain cleaning, repipe, reviews, service area, contact.

## Status
Backend + migrations: **built & boot-tested.** n8n: 4 workflows built, WF-5 spec'd.
Storyblok: components built & typechecked; Next.js app + pages: **to build.**
See `CLAUDE.md` for the full verified-vs-todo breakdown.
