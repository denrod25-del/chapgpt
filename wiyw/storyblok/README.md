# WiYW Storyblok Component Set

Headless CMS blocks for the What's in Your Water site (Next.js App Router + Storyblok).
Design tokens grounded in the water-testing subject — not the plumbing-blue cliché or the
AI-default cream/terracotta look. Signature element: the **Water Test Readout** hardness gauge.

## Design system (tokens.css)
- Palette: aquifer navy `#0B1F2A`, tested-cyan `#12B0C9` (single bold accent), mineral off-white
  `#F5F7F6`, hardness amber `#E8A13A`, slate `#5A6B72`.
- Type: Fraunces (display) / Inter (body) / JetBrains Mono (data — GPG, prices, test results).
- Signature: hardness gauge marker on a 0–22 GPG scale, reused hero + service pages.

## Files
- `tokens.css` — design tokens (import once, globally).
- `preview-homepage.html` — standalone static render of the full homepage. Open in a browser
  to see the design. Screenshots: `preview-desktop.png`, `preview-mobile.png`.
- `component-schemas.json` — Storyblok block schemas (17 blocks). Recreate in the Block Library
  or import via Management API.
- `storyblok.ts` — SDK init + component registry (block name → React component).
- `components/*.tsx` — React implementations. Verified: typechecks clean.

## Blocks (17)
Structural: `page` (root, holds SEO + schema_type + body).
Hero: `hero` (standard/emergency variants), `water_test_readout` (signature).
Services: `service_grid` + `service_grid_item`, `service_block` (problem/solution/process).
Pricing: `price_band` + `price_tier` (real PBC bands: city $1,200–$2,800, well $3,500–$6,500).
Trust/convert: `why_test`, `testimonial_row` + `testimonial`, `faq` + `faq_item` (emits FAQPage
JSON-LD), `service_area`, `cta_band`, `trust_strip`, `contact_form` (posts to backend /leads).

## Setup
1. `npm i @storyblok/react storyblok-rich-text-react-renderer`
2. Create the blocks in Storyblok (from `component-schemas.json`).
3. Register in your root layout:
   ```ts
   import { getStoryblok } from "./storyblok";
   getStoryblok();
   ```
4. Set env: `STORYBLOK_TOKEN` (CDA read token), `NEXT_PUBLIC_API_BASE` (FastAPI base URL).
5. Import `tokens.css` globally; port the CSS from `preview-homepage.html` into your stylesheet
   (the preview's `<style>` block is the reference implementation of every block's classes).

## Wiring notes
- `contact_form` posts to `${NEXT_PUBLIC_API_BASE}/leads` with `source=website`, captures
  `landing_page`, sets `urgency` from the block's `urgency_default` (emergency pages → emergency
  flow). Client-side E.164 check mirrors the backend to avoid 422 round-trips.
- `faq` emits FAQPage structured data — set the page `schema_type` to FAQPage on FAQ-heavy pages.
- `page.seo_title` pattern: `[Service] in [City] | What's in Your Water` (≤60 chars).
- Storyblok publish webhook → your `/webhooks/storyblok` (already built) → sitemap rebuild + GSC ping.

## Page assembly (maps to KEYWORD_MAP.md build order)
Homepage = hero(standard) + service_grid + why_test + price_band + testimonial_row + cta_band.
Emergency = hero(emergency) + service_block(problem) + contact_form(urgency=emergency) + testimonial_row.
Service page = hero + service_block×3 + price_band + faq + testimonial_row + cta_band.
Well-water page = hero + why_test(well angle) + service_block + price_band(well tiers) + faq + cta_band.
