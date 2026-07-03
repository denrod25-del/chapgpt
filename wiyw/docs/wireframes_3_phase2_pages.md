# WiYW — Page Wireframes & Copy Outlines (Set 3, Phase 2)

Six pages: Reverse Osmosis, Drain Cleaning, Repipe (service pages) + Reviews, Service Area,
Contact (utility/conversion pages). Same depth as Sets 1–2. Verified market facts (June 2026).

Shared conventions carry over: sticky header + phone, Service/LocalBusiness/FAQPage schema on
service pages, NAP footer, one primary keyword per page, phone above fold (fires `call_clicked`),
forms post to `/leads` with `source=website`.

================================================================================
## 1. REVERSE OSMOSIS PAGE   → /reverse-osmosis
================================================================================

**Primary keyword:** `reverse osmosis system palm beach county` (H2: `under sink water filter [city]`)
**Support:** `ro drinking water system`, `pfas reverse osmosis`, `ro system installation [city]`
**Page goal:** Book a free water test → RO install quote. **Primary conversion:** form; call secondary.
**Buyer:** homeowner who wants clean *drinking* water specifically — often arrives from the filtration
or well-water page. Lower ticket, quick decision, strong upsell/attach to softener+filter jobs.

### Storyblok block order
`hero(standard)` → `service_block(problem)` → `why_test(drinking-water focus)` →
`service_block(solution)` → `price_band` → `faq` → `testimonial_row` → `cta_band`

### Wireframe
```
┌───────────────────────────────────────────────┐
│ STICKY: logo · nav · [Call (561)...]           │
├───────────────────────────────────────────────┤
│ HERO (standard)                                 │
│  eyebrow: Palm Beach County · Reverse Osmosis    │
│  H1: Reverse Osmosis Drinking Water Systems in   │
│      Palm Beach County                           │
│  sub: The final polish — bottled-quality water   │
│       from your kitchen tap.                     │
│  [Book a Free Water Test] [Call]                 │
├───────────────────────────────────────────────┤
│ PROBLEM: what whole-house filters DON'T catch;    │
│  why drinking water gets its own stage            │
├───────────────────────────────────────────────┤
│ WHY TEST: PFAS + dissolved solids RO removes      │
├───────────────────────────────────────────────┤
│ SOLUTION: under-sink RO; pairs with softener/     │
│  filter (cross-link both)                         │
├───────────────────────────────────────────────┤
│ PRICE BAND: RO install; combo attach              │
├───────────────────────────────────────────────┤
│ FAQ (schema) → REVIEWS → CTA → FOOTER             │
└───────────────────────────────────────────────┘
```

### CTA placement
Hero dual CTA; sticky call; CTA band after reviews. Inline cross-links to filtration + softener
(RO is the drinking-water stage of a fuller system — complementary, not competing).

### Trust elements
License #, insured, free test, EPA-recognized PFAS treatment (RO is the most complete), honest
"you may not need this if..." framing, food-grade components.

### SEO notes
- Title: `Reverse Osmosis Drinking Water Systems in Palm Beach County | What's in Your Water`
- Primary keyword in H1; keep distinct from filtration page (whole-house vs point-of-use drinking).
- Schema: Service + LocalBusiness + FAQPage.
- RO is the EPA-named "most complete" PFAS removal — accurate, authoritative, links from filtration.

### Conversion notes
- Natural attach to softener/filter jobs — mention the bundle, don't force it.
- Lower ticket = shorter consideration; keep the page tight and the CTA close.
- Form prefilled `ro_system`.

### Copy — Hero
> **Eyebrow:** Palm Beach County · Reverse Osmosis
> **H1:** Reverse Osmosis Drinking Water Systems in Palm Beach County
> **Sub:** A whole-house filter cleans the water in your pipes. Reverse osmosis polishes the water
> you actually drink — installed under your kitchen sink, bottled-quality from the tap.
> **Primary CTA:** Book a Free Water Test · **Secondary:** Call (561) 555-0100

### Copy — Problem block
> **H2:** Why drinking water gets its own stage
> A whole-house carbon filter handles chlorine, sediment, and reduces contaminants across every tap.
> But for the water you drink and cook with, you want the most thorough removal possible — dissolved
> solids, PFAS, and anything a carbon filter only reduces. That's a job for reverse osmosis at the
> point of use, not the whole house.

### Copy — Why-Test block (drinking-water focus)
> **H2:** What reverse osmosis removes
> RO pushes water through a semi-permeable membrane that removes dissolved solids, and it's the
> EPA-recognized method that removes PFAS most completely — more thoroughly than carbon or anion
> exchange alone. If your test shows PFAS, high dissolved solids, or you simply want the cleanest
> drinking water in the house, RO is the answer. If it doesn't, we'll tell you a filter is enough.
> **Chips:** PFAS · Dissolved solids · Lead · Taste · Odor

### Copy — Solution block
> **H2:** Under-sink RO, paired with your system
> We install RO at the kitchen sink with its own faucet, so drinking and cooking water is polished
> without slowing the rest of the house. It works best downstream of a softener (hardness shortens
> membrane life) and a carbon filter (which protects the membrane). If you're already getting a
> softener or whole-house filter, adding RO is a small step for the biggest quality jump on the water
> you consume. (See our softener and filtration pages.)

### Copy — Price band
> **Heading:** What reverse osmosis costs
> - Under-sink RO system, installed — **priced per system**
> - Added to a softener or filter install — **reduced combined pricing**
> **Disclaimer:** Final scope after a free in-home test. We only recommend RO if your water needs it.

### Copy — FAQ
> **Q: Does reverse osmosis remove PFAS?**
> Yes — RO is the most complete PFAS removal method the EPA recognizes, more thorough than carbon
> alone. It's the best choice if your test shows PFAS in your drinking water.
> **Q: Do I need RO if I have a whole-house filter?**
> They do different jobs. The whole-house filter treats every tap; RO polishes drinking water to the
> highest level at the kitchen sink. Many homes run both.
> **Q: Does RO waste water?**
> Modern systems are far more efficient than older ones. We size the unit to your usage and can
> recommend high-efficiency models that minimize wastewater.
> **Q: Where does it install?**
> Under your kitchen sink, with a dedicated drinking-water faucet. Installation is quick and doesn't
> affect the rest of your plumbing.

================================================================================
## 2. DRAIN CLEANING PAGE   → /drain-cleaning
================================================================================

**Primary keyword:** `drain cleaning palm beach county` (H2: `clogged drain [city]`)
**Support:** `sewer line cleaning [city]`, `slow drain repair`, `hydro jetting [city]`,
`main line clog`
**Page goal:** Book drain service. **Primary conversion:** call (clogs are semi-urgent) → form second.
**Buyer:** homeowner with a slow/clogged/backing-up drain. Commodity plumbing, competitive, high intent,
fast decision. Funds the water-treatment side; steady volume.

### Storyblok block order
`hero(standard, call-leaning)` → `service_block(problem)` → `service_block(solution)` →
`price_band` → `service_block(process)` → `faq` → `testimonial_row` → `cta_band`

### Wireframe
```
┌───────────────────────────────────────────────┐
│ STICKY: logo · nav · [Call (561)...]           │
├───────────────────────────────────────────────┤
│ HERO (standard, call primary)                    │
│  eyebrow: Palm Beach County · Drain Cleaning     │
│  H1: Drain Cleaning in Palm Beach County         │
│  sub: Slow drains, clogs, and backups — cleared  │
│       fast with upfront flat-rate pricing.       │
│  [Call Now] [Book a Visit]                        │
├───────────────────────────────────────────────┤
│ PROBLEM: slow drain · recurring clog · backup ·   │
│  multiple drains = main line                      │
├───────────────────────────────────────────────┤
│ SOLUTION: snake vs hydro jetting; camera          │
│  inspection for recurring clogs                   │
├───────────────────────────────────────────────┤
│ PRICE BAND: standard clear / main line / jetting  │
├───────────────────────────────────────────────┤
│ PROCESS: diagnose → clear → camera → prevent       │
├───────────────────────────────────────────────┤
│ FAQ (schema) → REVIEWS → CTA → FOOTER             │
└───────────────────────────────────────────────┘
```

### CTA placement
Call primary in hero (semi-urgent); sticky call; book-a-visit for non-urgent. CTA band after reviews.

### Trust elements
License #, insured, flat-rate upfront pricing (no per-hour surprises), camera inspection option,
same-day availability, "we tell you if it's a bigger problem" honesty.

### SEO notes
- Title: `Drain Cleaning in Palm Beach County | What's in Your Water`
- Primary keyword H1; `hydro jetting` and `main line clog` as H2s (higher-ticket intents).
- Schema: Service + LocalBusiness + FAQPage.
- Commodity term, competitive — win on transparency (flat-rate) and camera-inspection depth.

### Conversion notes
- Semi-urgent → phone-first, but not full emergency styling (that's the emergency page).
- The "multiple slow drains = main line" hook upsells camera inspection honestly.
- Form prefilled `drain`.

### Copy — Hero
> **Eyebrow:** Palm Beach County · Drain Cleaning
> **H1:** Drain Cleaning in Palm Beach County
> **Sub:** Slow drains, stubborn clogs, and backups cleared fast — with flat-rate pricing you
> approve before we start. No hourly surprises.
> **Primary CTA:** Call (561) 555-0100 · **Secondary:** Book a Visit

### Copy — Problem block
> **H2:** What your drains are telling you
> A single slow drain is usually a local clog — hair, grease, soap. But when several drains slow down
> at once, or the lowest drain in the house backs up, that points to the main line, not one fixture.
> Recurring clogs in the same spot often mean something deeper: roots, a belly in the pipe, or
> buildup a plunger can't reach. Knowing the difference is the difference between a quick clear and
> paying twice.

### Copy — Solution block
> **H2:** The right tool for the clog
> Most clogs clear with a professional auger. Grease and heavy buildup — especially in kitchen and
> main lines — often need hydro jetting, which scours the pipe walls clean rather than just punching
> a hole through. For anything recurring, we run a camera to see exactly what's going on before we
> quote a fix, so you're not guessing and neither are we.

### Copy — Price band
> **Heading:** Drain cleaning pricing in Palm Beach County
> - Standard drain clear — **flat-rate, quoted upfront**
> - Main line clog — **priced after diagnosis**
> - Hydro jetting — **for grease/root buildup, quoted on site**
> - Camera inspection — **added for recurring clogs**
> **Disclaimer:** Flat-rate pricing shown before work begins. You approve the number first.

### Copy — Process block (steps)
> Diagnose — we locate the clog and identify local vs main line.
> Clear it — auger or hydro jetting, matched to the blockage.
> Camera check — for recurring clogs, we show you the cause.
> Prevention advice — what to avoid so it doesn't come back.

### Copy — FAQ
> **Q: Why do my drains keep clogging in the same place?**
> Recurring clogs usually mean something structural — roots, a low spot in the pipe, or heavy
> buildup. A camera inspection finds the cause so you fix it once instead of clearing it monthly.
> **Q: What's the difference between snaking and hydro jetting?**
> A snake (auger) punches through a clog; hydro jetting scours the whole pipe wall clean. Grease and
> roots usually need jetting for a lasting fix.
> **Q: All my drains are slow at once — what does that mean?**
> That points to the main line rather than a single fixture. It's worth addressing quickly before it
> becomes a full backup.
> **Q: Do you offer flat-rate pricing?**
> Yes. You get the price before we start — no hourly meter, no surprises on the invoice.

================================================================================
## 3. REPIPE PAGE   → /repipe
================================================================================

**Primary keyword:** `whole house repipe palm beach county` (H2: `repiping [city]`)
**Support:** `polybutylene pipe replacement`, `repipe cost`, `old pipes leaking`,
`pinhole leaks copper`
**Page goal:** Book an assessment/quote. **Primary conversion:** form → call. **Buyer:** homeowner
with recurring leaks, old/failing pipes (polybutylene, aging copper), low water pressure, or
discolored water. High ticket, considered decision, longer read. Lower volume, high value.

### Storyblok block order
`hero(standard)` → `service_block(problem)` → `service_block(solution)` → `price_band` →
`service_block(process)` → `faq` → `testimonial_row` → `cta_band`

### Wireframe
```
┌───────────────────────────────────────────────┐
│ STICKY: logo · nav · [Call (561)...]           │
├───────────────────────────────────────────────┤
│ HERO (standard)                                 │
│  eyebrow: Palm Beach County · Whole-House Repipe │
│  H1: Whole-House Repiping in Palm Beach County   │
│  sub: Recurring leaks, low pressure, or old      │
│       polybutylene? Replace it once, done right. │
│  [Book an Assessment] [Call]                      │
├───────────────────────────────────────────────┤
│ PROBLEM: signs you need a repipe — pinhole leaks, │
│  polybutylene, rusty water, pressure loss         │
├───────────────────────────────────────────────┤
│ SOLUTION: full repipe in modern materials;        │
│  minimal-disruption approach                      │
├───────────────────────────────────────────────┤
│ PRICE BAND: assessment-based; financing note      │
├───────────────────────────────────────────────┤
│ PROCESS: assess → plan → repipe → patch → inspect │
├───────────────────────────────────────────────┤
│ FAQ (schema) → REVIEWS → CTA → FOOTER             │
└───────────────────────────────────────────────┘
```

### CTA placement
Hero (book assessment primary — this is a considered purchase); sticky call; CTA band after reviews.
High-ticket buyers want an assessment, not an instant quote — frame the CTA that way.

### Trust elements
License #, insured, "replace once, warrantied," modern materials, minimal-disruption process,
walls-patched-and-restored, financing available, upfront fixed quote after assessment.

### SEO notes
- Title: `Whole-House Repiping in Palm Beach County | What's in Your Water`
- Primary keyword H1; `polybutylene pipe replacement` and `pinhole leaks` as H2s (specific,
  high-intent — polybutylene is a known FL problem in older homes).
- Schema: Service + LocalBusiness + FAQPage.
- High-ticket, low-volume — depth and trust matter more than speed. Don't shorten.

### Conversion notes
- Considered purchase → lead with the assessment offer, not a price.
- Financing mention reduces sticker shock (competitors offer 100% financing — match it).
- Form prefilled `repipe`.

### Copy — Hero
> **Eyebrow:** Palm Beach County · Whole-House Repipe
> **H1:** Whole-House Repiping in Palm Beach County
> **Sub:** If you're chasing recurring leaks, fighting low pressure, or living with old polybutylene
> pipes, repiping replaces the problem at the root — once, done right, warrantied.
> **Primary CTA:** Book an Assessment · **Secondary:** Call (561) 555-0100

### Copy — Problem block
> **H2:** Signs it's time to repipe
> Pinhole leaks that keep showing up in different spots. Water pressure that's dropped across the
> house. Rusty or discolored water. And in a lot of older Palm Beach County homes, polybutylene pipe
> — a material used through the '80s and '90s that becomes brittle and fails without warning.
> Patching one leak at a time on failing pipe is money down the drain. A repipe ends the cycle.

### Copy — Solution block
> **H2:** Replace it once, in modern materials
> A whole-house repipe swaps your failing pipes for modern materials that won't corrode or go
> brittle. We plan the routes to minimize wall openings, protect your home during the work, and patch
> and restore everything we open. You get a house that's done — no more waiting for the next leak.

### Copy — Price band
> **Heading:** What a repipe costs in Palm Beach County
> - Whole-house repipe — **fixed quote after assessment**
> - Financing available — **spread the cost over time**
> **Disclaimer:** Repipe scope depends on your home's size, layout, and existing pipe. We assess
> first, then give you one fixed price — no open-ended billing.

### Copy — Process block (steps)
> On-site assessment — we map your plumbing and existing pipe material.
> Fixed-price plan — one quote, routes chosen to minimize disruption.
> Repipe — modern materials, your water kept on as much as possible.
> Patch & restore — we close and finish every wall we open.
> Final inspection — pressure-tested and verified before we're done.

### Copy — FAQ
> **Q: How do I know if I have polybutylene pipe?**
> It's usually gray plastic pipe, common in homes built or plumbed from the late '70s through mid
> '90s. If you're not sure, our assessment identifies it — and if you have it, replacing it is worth
> prioritizing, since it fails without warning.
> **Q: How long does a repipe take?**
> Most whole-house repipes are completed in a few days, depending on home size and layout. We keep
> your water on as much as possible and restore everything we open.
> **Q: Will you damage my walls?**
> We plan routes to minimize openings, and we patch and restore every wall we access as part of the
> job — you're not left with holes to fix.
> **Q: Is financing available?**
> Yes. A repipe is a big-ticket fix, so we offer financing to spread the cost rather than paying it
> all up front.

================================================================================
## 4. REVIEWS PAGE   → /reviews
================================================================================

**Primary keyword:** `what's in your water reviews` (brand term; also captures `[brand] palm beach reviews`)
**Page goal:** Convert trust into a call/booking. **Primary conversion:** call/CTA after reading proof.
**Buyer:** someone comparison-shopping who's checking legitimacy before calling. Not a keyword-volume
play — it's a conversion-support page linked from every other page.

### Storyblok block order
`hero(standard, minimal)` → `testimonial_row` (multiple, grouped) → `trust_strip` → `cta_band`

### Wireframe
```
┌───────────────────────────────────────────────┐
│ STICKY: logo · nav · [Call (561)...]           │
├───────────────────────────────────────────────┤
│ HERO (compact)                                  │
│  eyebrow: Palm Beach County                      │
│  H1: What Our Neighbors Say                       │
│  sub: Real reviews from real Palm Beach County    │
│       homes — water treatment and plumbing.       │
│  aggregate rating (★ 5.0 · N reviews)             │
├───────────────────────────────────────────────┤
│ TESTIMONIAL ROWS (grouped by service)             │
│  Water treatment · Well water · Plumbing/heater   │
│  each with name + neighborhood + rating           │
├───────────────────────────────────────────────┤
│ TRUST STRIP: Licensed · Insured · Google rating   │
├───────────────────────────────────────────────┤
│ CTA BAND: "Join them — book a free test" + FOOTER │
└───────────────────────────────────────────────┘
```

### CTA placement
CTA band between review groups (trust peaks) and at the bottom. Sticky call throughout.

### Trust elements
Aggregate star rating, real names + neighborhoods (local proof), review platform badges (Google),
mix of service types so every buyer sees themselves. Respond-to-100%-of-reviews policy referenced.

### SEO notes
- Title: `Reviews — What's in Your Water | Palm Beach County`
- Emit `Review`/`AggregateRating` schema (Storyblok testimonial block can carry rating → JSON-LD).
- Not a volume keyword page — it's linked from all service pages as trust support. Brand-term capture.
- Reviews here mirror what WF-5 syncs from Semrush monitoring into Postgres `reviews`.

### Conversion notes
- Group reviews by service so softener buyers, well buyers, and plumbing buyers each find relevant proof.
- Include neighborhood names — reinforces local + service area, subtle SEO value.
- Keep the page fast and skimmable; the job is reassurance, then a nudge to call.

### Copy — Hero
> **Eyebrow:** Palm Beach County
> **H1:** What our neighbors say
> **Sub:** Real reviews from real homes across Palm Beach County — water treatment, well water, and
> plumbing. We respond to every one.

### Copy — Testimonial groups (samples — pull live reviews via WF-5)
> **Water treatment**
> ★★★★★ "Finally understood why my old softener never worked — sized for the wrong hardness. New
> one's perfect." — Priya S., Wellington
> **Well water**
> ★★★★★ "They tested our well before recommending anything. Turned out we needed iron treatment, not
> just a softener. No hard sell." — Marcus T., Loxahatchee
> **Plumbing & water heaters**
> ★★★★★ "Water heater died on a Sunday. Real person answered, gave an arrival window, fixed it same
> day." — Dana R., Boca Raton

### Copy — CTA band
> **Heading:** Join your neighbors — find out what's in your water, free.
> **CTA:** Book a Free Water Test

================================================================================
## 5. SERVICE AREA PAGE   → /service-area
================================================================================

**Primary keyword:** `plumber palm beach county service area` (supports local relevance broadly)
**Page goal:** Confirm coverage + route to service pages. **Primary conversion:** call/form once
coverage confirmed. **Buyer:** checking "do they come to my area?" before calling. Also an
SEO hub that links out to future city×service pages.

### Storyblok block order
`hero(standard, minimal)` → `service_area` (full city list + map) → `service_grid` →
`trust_strip` → `cta_band`

### Wireframe
```
┌───────────────────────────────────────────────┐
│ STICKY: logo · nav · [Call (561)...]           │
├───────────────────────────────────────────────┤
│ HERO (compact)                                  │
│  eyebrow: Palm Beach County, FL                  │
│  H1: Where We Work                                │
│  sub: Water treatment and plumbing across Palm    │
│       Beach County — coast to the western wells.  │
├───────────────────────────────────────────────┤
│ SERVICE AREA: map + full city list, split         │
│  Coastal corridor | Western well-water pockets    │
├───────────────────────────────────────────────┤
│ SERVICE GRID: links to all service pages          │
│  (this page is a hub — route people onward)       │
├───────────────────────────────────────────────┤
│ TRUST STRIP → CTA BAND → FOOTER NAP               │
└───────────────────────────────────────────────┘
```

### CTA placement
CTA band after the city list; sticky call. The job is "yes we cover you → now call."

### Trust elements
Full city list (comprehensiveness = credibility), map, NAP, license #, western-well specialty callout.

### SEO notes
- Title: `Service Area — Palm Beach County Water Treatment & Plumbing | What's in Your Water`
- This is the hub for future `/[service]/[city]` pages (Phase 3). Link out as those get built.
- Split coastal vs western framing reinforces the well-water differentiation.
- Schema: LocalBusiness with `areaServed` listing the cities.

### Conversion notes
- Comprehensive list answers "do they cover me?" instantly — don't make people hunt.
- Route onward: service grid turns a coverage-check visit into a service-page visit.
- Western well-water callout captures the differentiated, high-value segment.

### Copy — Hero
> **Eyebrow:** Palm Beach County, FL
> **H1:** Where we work
> **Sub:** We serve water treatment and plumbing across Palm Beach County — from the coastal cities
> to the private wells out west.

### Copy — Service area block
> **Heading:** Serving all of Palm Beach County
> **Coastal corridor:** West Palm Beach · Boca Raton · Delray Beach · Boynton Beach · Jupiter · Palm
> Beach Gardens · Lake Worth · Wellington
> **Western well-water pockets:** Loxahatchee · The Acreage · Royal Palm Beach · Westlake · Belle
> Glade · Pahokee
> **Note:** West of the Turnpike, most homes are on private wells with iron, sulfur, and hardness —
> that's our specialty, and it's why we test before we quote.

### Copy — CTA band
> **Heading:** In our service area? Find out what's in your water — free.
> **CTA:** Book a Free Water Test

================================================================================
## 6. CONTACT PAGE   → /contact
================================================================================

**Primary keyword:** `what's in your water contact` / `[brand] palm beach phone` (brand/nav term)
**Page goal:** Capture the lead or drive the call. **Primary conversion:** form submit OR call —
this is the terminal conversion page. Keep friction near zero.
**Buyer:** ready to act. Don't sell — make it effortless to reach you.

### Storyblok block order
`hero(standard, minimal)` → `contact_form` → `service_area(compact)` → `trust_strip`

### Wireframe
```
┌───────────────────────────────────────────────┐
│ STICKY: logo · nav · [Call (561)...]           │
├───────────────────────────────────────────────┤
│ HERO (compact)                                  │
│  eyebrow: Palm Beach County                      │
│  H1: Get in Touch                                 │
│  sub: Book a free water test or reach us for any  │
│       plumbing job. Real people, fast response.   │
├───────────────────────────────────────────────┤
│ CONTACT FORM (primary) | phone + hours sidebar    │
│  name · phone · email · service → [Submit]        │
│  posts to /leads (source=website)                 │
├───────────────────────────────────────────────┤
│ SERVICE AREA (compact) + map                      │
├───────────────────────────────────────────────┤
│ TRUST STRIP → FOOTER NAP                          │
└───────────────────────────────────────────────┘
```

### CTA placement
The form IS the CTA. Phone prominent alongside for call-preferrers. Sticky call throughout. No
competing CTAs — this page has one job.

### Trust elements
Phone, hours, NAP, license #, "real person answers," response-time promise, free-test offer.

### SEO notes
- Title: `Contact — What's in Your Water | Palm Beach County Water Treatment & Plumbing`
- Schema: LocalBusiness with full NAP, `openingHours`, `telephone`, `areaServed`.
- Terminal page — minimal SEO ambition, maximal conversion clarity.

### Conversion notes
- 3–4 field form only (name/phone/email/service) — every extra field drops completion.
- Form success state shows the "we'll call you shortly" message (already built in ContactForm.tsx).
- Emergency selector in the form routes to `urgency=emergency` → fast-response flow.
- Phone above the form for call-preferrers; both paths land in the same `/leads` pipeline.

### Copy — Hero
> **Eyebrow:** Palm Beach County
> **H1:** Get in touch
> **Sub:** Book a free water test or reach us for any plumbing job. A real person answers, and we
> respond fast.

### Copy — Contact form
> **Heading:** Tell us what you need
> Fields: Your name · Phone · Email (optional) · What can we help with? (service dropdown)
> **Button:** Request my free test
> **Success state:** "Got it — we'll call you shortly. Need us now? Call (561) 555-0100."

### Copy — Sidebar (phone + hours)
> **Call:** (561) 555-0100 — a real person, not an answering service
> **Hours:** [business hours] · Emergency service available 24/7
> **Serving:** All of Palm Beach County

================================================================================
## Phase 2 cross-linking additions (extends Set 2 map)
================================================================================
- RO ⇄ Filtration ⇄ Softener (drinking-water polish completes the treatment train)
- Drain → Emergency (backups that won't clear → emergency page)
- Repipe → Water Heater (whole-home plumbing work often surfaces heater age)
- Reviews ← every service page (trust support, linked site-wide)
- Service Area ← every page footer; → all service pages (hub-and-spoke)
- Contact ← every CTA that isn't a phone tap; terminal conversion node
- All Phase-2 service pages → Contact + Reviews + Service Area (consistent with Phase-1)
```
