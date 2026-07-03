# WiYW — Build Order (Claude Code task sequence)

Sequenced so each step unblocks the next. Backend is already boot-tested, so the critical path is
frontend + wiring + deploy. Check off as you go.

## Phase 0 — Environment (½ day)
- [ ] Provision Postgres (Coolify/Docker on the VPS). Confirm `pgcrypto` available.
- [ ] Apply migrations 001–005 in order. Verify `SELECT * FROM tags;` returns the seeded tags.
- [ ] Fill `backend/.env` with real keys: DATABASE_URL, RESEND_API_KEY, GATEWAYAPI_TOKEN,
      OWNER_ALERT_PHONE, BRAND_PHONE. (Brevo/Mailgun/Storyblok can come later.)
- [ ] `uvicorn app.main:app` → `/health` returns ok. Smoke-test `POST /leads` with a real payload.

## Phase 1 — Site shell + core pages (2–3 days)  ← critical path
- [ ] Scaffold Next.js App Router project. Install `@storyblok/react`,
      `storyblok-rich-text-react-renderer`.
- [ ] Mount the component registry from `storyblok/storyblok.ts` in root layout.
- [ ] Port the CSS from `storyblok/preview-homepage.html` `<style>` into a global stylesheet;
      import `storyblok/tokens.css`.
- [ ] Create the 17 blocks in Storyblok from `storyblok/component-schemas.json`.
- [ ] Set env: STORYBLOK_TOKEN (CDA read), NEXT_PUBLIC_API_BASE (FastAPI URL).
- [ ] Build **Homepage** in Storyblok from `docs/wireframes_1...` (blocks already defined). Verify
      it renders and matches `preview-homepage.html`.
- [ ] Build **Emergency**, **Water Softener**, **Well Water**, **Filtration**, **Water Heater**
      pages from `docs/wireframes_1` + `docs/wireframes_2`.
- [ ] Confirm `contact_form` POSTs to `/leads` and the success state shows.
- [ ] Wire Storyblok publish webhook → `/webhooks/storyblok` → sitemap rebuild + GSC ping
      (the handler is stubbed in `backend/app/routers/webhooks.py` — implement the sitemap regen).

## Phase 2 — Comms live (1 day)
- [ ] Verify Resend domain (`mail.whatsinyourwater.com`), add SPF/DKIM/DMARC. Test confirmation.
- [ ] GatewayAPI: sender ID + credit + delivery webhook → `/webhooks/gatewayapi`. Test SMS + STOP.
- [ ] Configure Mailgun failover subdomain (`mg.`) + inbound route → `/webhooks/mailgun`.
- [ ] End-to-end test: submit a real lead → confirmation email + SMS arrive → owner alert fires →
      lead + event + tags land in Postgres.

## Phase 3 — Automations (1 day)
- [ ] Import n8n workflows wf1–wf4; remap credentials + REPLACE_* placeholders; point at Postgres.
- [ ] Build WF-5 (review monitoring) from `n8n/WF5_review_monitoring.md`.
- [ ] Test each: create a booking → reminder fires in window; complete a job → review request fires.

## Phase 4 — Brevo + SEO (1–2 days)
- [ ] Brevo: verify domain, create lists/segments/attributes per `docs/BREVO_SETUP.md`.
      Confirm `backend/app/services/brevo.py` upserts contacts into list_leads.
- [ ] Build the Brevo nurture/review/reactivation email templates; wire n8n email legs to them.
- [ ] Google Search Console: verify domain (DNS), submit sitemap.
- [ ] Semrush: project `plumbing-main-pbc`, Position Tracking (per `docs/KEYWORD_MAP.md`), Listing
      Management, review monitoring (feeds WF-5).
- [ ] Optimize GBP per KEYWORD_MAP (categories, NAP, posts, seeded Q&A).

## Phase 5 — Phase-2 pages + polish (2–3 days)
- [ ] Build RO, drain, repipe, reviews, service area, contact pages from `docs/wireframes_3`.
- [ ] Implement internal cross-linking per the maps at the end of wireframes_2 and _3.
- [ ] Add `Review`/`AggregateRating` schema on the reviews page (pull from Postgres `reviews`).
- [ ] Accessibility + mobile pass (preview already responsive; verify built pages).

## Phase 6 — Deploy + verify (1 day)
- [ ] Dockerize + deploy backend (Dockerfile provided) to Coolify.
- [ ] Deploy Next.js (Vercel or Coolify).
- [ ] Point DNS; confirm SSL; confirm all webhooks reachable from providers.
- [ ] Final end-to-end: real lead from the live site → full pipeline → owner alert.

## Notes
- Backend is boot-tested — don't rewrite it; extend it. If you touch it, honor NASA-light (CLAUDE.md).
- Never wire a campaign into Resend or a receipt into Brevo (docs/OWNERSHIP.md).
- The highest-ROI content is the well-water pages (Loxahatchee/Acreage/Wellington) — prioritize
  those for early SEO wins per KEYWORD_MAP.
- Don't build city×service pages (Phase 3 SEO) until the core service pages rank — thin doorway
  pages get penalized.
