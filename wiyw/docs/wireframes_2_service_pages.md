# WiYW — Service Page Wireframes & Copy Outlines (Set 2)

Four Tier-1 money pages: Water Softener, Well Water Treatment, Whole-House Filtration, Water Heater.
Same depth as the homepage/emergency pair. Every page maps to Storyblok blocks and a keyword
cluster from KEYWORD_MAP.md. Prices, hardness, and contaminant facts are verified (June 2026).

Shared conventions:
- Block order noted per page maps to `component-schemas.json` block names.
- Every page: sticky header w/ phone, Service + LocalBusiness + FAQPage schema, NAP footer.
- One primary keyword per page — no cannibalization. Support terms live in H2s.
- Phone above the fold (tel: fires `call_clicked`); form posts to `/leads` with `source=website`.

================================================================================
## 1. WATER SOFTENER PAGE   → /water-softener
================================================================================

**Primary keyword:** `water softener installation palm beach county`
**Support:** `water softener cost south florida`, `what size water softener do i need florida`,
`hard water palm beach`, `48000 grain water softener`
**Page goal:** Book a free water test → softener install quote. **Primary conversion:** form; call secondary.
**Buyer:** city-water homeowner with scale/soap-scum/dry-skin symptoms; price-aware, comparison-shopping.

### Storyblok block order
`hero(standard)` → `water_test_readout` → `service_block(problem)` → `service_block(solution)` →
`why_test` → `price_band` → `service_block(process)` → `faq` → `testimonial_row` → `cta_band`

### Wireframe
```
┌───────────────────────────────────────────────┐
│ STICKY: logo · nav · [Call (561)...]           │
├───────────────────────────────────────────────┤
│ HERO (standard, dual CTA)                       │
│  eyebrow: Palm Beach County · Water Softeners   │
│  H1: Water Softener Installation in Palm Beach   │
│      County                                      │
│  sub: Sized for real Biscayne Aquifer hardness — │
│       not national guesswork.                    │
│  [Book a Free Water Test] [Call]                 │
│  readout: 18 GPG gauge (signature)               │
├───────────────────────────────────────────────┤
│ PROBLEM: "Why your water is so hard here"        │
│  15–22 GPG · scale · dead water heaters · scum   │
├───────────────────────────────────────────────┤
│ SOLUTION: "The right-sized softener"             │
│  48k-grain vs 32k explainer · ion exchange       │
├───────────────────────────────────────────────┤
│ WHY TEST: test-first differentiator + chips      │
├───────────────────────────────────────────────┤
│ PRICE BAND: city / +carbon / combo tiers         │
├───────────────────────────────────────────────┤
│ PROCESS: test → size → install (2–4h) → set      │
├───────────────────────────────────────────────┤
│ FAQ (emits FAQPage schema)                        │
├───────────────────────────────────────────────┤
│ REVIEWS (softener-specific, local)               │
├───────────────────────────────────────────────┤
│ CTA BAND + FOOTER NAP                             │
└───────────────────────────────────────────────┘
```

### CTA placement
Hero dual CTA; sticky call; repeat CTA band after reviews (trust peak). Form near footer as catch.

### Trust elements
License #, insured, Google rating, "free in-home test," sizing-done-right guarantee, brand names
installed (state which — matters vs Hague/Kinetico dealers).

### SEO notes
- Title: `Water Softener Installation in Palm Beach County | What's in Your Water` (≤60 chars — tight)
- H1 = primary keyword, natural. Support terms as H2 ("What size softener do I need?").
- Schema: Service + LocalBusiness + FAQPage.
- The 48k-vs-32k grain angle is a content wedge competitors miss — own it in an H2.

### Conversion notes
- Readout gauge is the scroll-stopper; keep it in hero.
- Price transparency up front beats competitors who hide pricing behind a form.
- Form: name/phone/service (prefilled `water_softener`).

### Copy — Hero
> **Eyebrow:** Palm Beach County · Water Softeners
> **H1:** Water Softener Installation in Palm Beach County
> **Sub:** Palm Beach County water runs 15–22 grains per gallon — nearly double the national
> average. We test your actual hardness, size the system right the first time, and install it in
> a single visit.
> **Primary CTA:** Book a Free Water Test · **Secondary:** Call (561) 555-0100

### Copy — Problem block
> **H2:** Why your water is so hard here
> Palm Beach County draws from the Biscayne Aquifer at 15–22 GPG. Anything above 7 GPG damages
> plumbing. That's the chalky buildup on fixtures, the soap that won't lather, the water heater
> that scales up and dies years early, and the film on your skin after a shower. A softener fixes
> the cause, not the symptoms.

### Copy — Solution block
> **H2:** The right-sized softener (why 32,000 grains isn't enough)
> National guides recommend a 32,000-grain system for a family of four. Those guides assume 7–10
> GPG water. Yours isn't that. At 15–22 GPG, a family of four needs a 48,000-grain system — run a
> 32k unit here and it operates at reduced capacity from day one, wears out early, and never fully
> softens. We size to your measured hardness, not an average.

### Copy — Process block (steps, one per line in the block)
> Free in-home water test — we measure your actual hardness and iron.
> Correct sizing — matched to your GPG and household size.
> Single-visit install — most softeners go in within 2–4 hours.
> Programmed to your water — set for your hardness, not a factory default.

### Copy — Price band
> **Heading:** What a water softener costs in Palm Beach County
> - City water softener — **$1,200–$2,800 installed**
> - With catalytic carbon pre-filter — **to $3,000** (removes chlorine/chloramine too)
> - Softener + filter + RO combo — **from $2,500**
> **Disclaimer:** Final price after your free in-home water test. No blind quotes.

### Copy — FAQ (each Q → FAQPage schema)
> **Q: What size water softener do I need in South Florida?**
> Most families of four need a 48,000-grain system because local water runs 15–22 GPG. The exact
> size depends on your measured hardness and daily usage — the free test settles it.
> **Q: How long does installation take?**
> Most installs take 2–4 hours in a single visit, including the bypass valve and programming.
> **Q: Salt-based or salt-free?**
> Salt-based ion exchange is the only method proven to remove hardness minerals. Salt-free
> "conditioners" reduce scale but don't soften. For 15–22 GPG water, we recommend salt-based.
> **Q: Do I need a softener if I'm on city water?**
> Yes. City water here still comes from the Biscayne Aquifer at 15–22 GPG. Hardness isn't removed
> by the utility.

### Copy — Reviews (softener-specific)
> ★★★★★ "Finally understood why my old softener never worked — it was sized for the wrong hardness.
> New one's perfect." — Priya S., Wellington

================================================================================
## 2. WELL WATER TREATMENT PAGE   → /well-water-treatment
================================================================================

**Primary keyword:** `well water treatment loxahatchee` (also target `the acreage`, `wellington well water`)
**Support:** `rotten egg smell water well`, `iron in well water`, `well water bacteria`,
`well water test palm beach`
**Page goal:** Book a free well-water test. **Primary conversion:** form; call secondary.
**Buyer:** western-PBC well owner with iron staining, sulfur smell, or health concern. Higher ticket
($3,500–$6,500), longer consideration. This is WiYW's differentiated, low-competition page — highest ROI.

### Storyblok block order
`hero(standard)` → `service_block(problem)` → `why_test(well angle)` → `service_block(solution)` →
`price_band(well tiers)` → `service_block(process)` → `faq` → `service_area(western PBC)` →
`testimonial_row` → `cta_band`

### Wireframe
```
┌───────────────────────────────────────────────┐
│ STICKY: logo · nav · [Call (561)...]           │
├───────────────────────────────────────────────┤
│ HERO (standard)                                 │
│  eyebrow: Loxahatchee · Acreage · Wellington    │
│  H1: Well Water Treatment for Western Palm       │
│      Beach County                                │
│  sub: Iron, sulfur, bacteria & hardness — tested │
│       and treated at the source.                 │
│  [Book a Free Well-Water Test] [Call]            │
├───────────────────────────────────────────────┤
│ PROBLEM: "What's really in your well"            │
│  iron stains · rotten-egg smell · bacteria       │
│  · nitrates · hardness — the full stack          │
├───────────────────────────────────────────────┤
│ WHY TEST (well angle): municipal PFAS rules       │
│  DON'T cover private wells — you're on your own   │
├───────────────────────────────────────────────┤
│ SOLUTION: multi-stage treatment train            │
│  pre-treat iron/sulfur → soften → filter/RO       │
├───────────────────────────────────────────────┤
│ PRICE BAND: well + iron pre-treatment tiers       │
├───────────────────────────────────────────────┤
│ PROCESS: comprehensive test → design → install    │
├───────────────────────────────────────────────┤
│ FAQ (schema)                                      │
├───────────────────────────────────────────────┤
│ SERVICE AREA: western PBC map + neighborhoods     │
├───────────────────────────────────────────────┤
│ REVIEWS (well-water specific) + CTA + FOOTER      │
└───────────────────────────────────────────────┘
```

### CTA placement
Hero; sticky call; CTA band after service area. Emphasize the *test* as the offer — well buyers
distrust blind quotes more than anyone (competitors upsell without testing).

### Trust elements
License #, insured, "we test before we quote," comprehensive well panel (iron/sulfur/bacteria/
nitrates/hardness), local neighborhood proof (Loxahatchee/Acreage names), no-oversell promise.

### SEO notes
- Title: `Well Water Treatment in Loxahatchee & The Acreage | What's in Your Water`
- H1 primary keyword; H2s for `rotten egg smell` (hydrogen sulfide), `iron in well water`.
- Schema: Service + LocalBusiness + FAQPage.
- The regulatory wedge (private wells excluded from federal PFAS rules) is unique, authoritative
  content — competitors don't cover it. Put it in the Why-Test block prominently.
- This page justifies its own city variants later (Wellington, Loxahatchee) once it ranks.

### Conversion notes
- Higher ticket = longer read. Depth builds trust; don't shorten.
- Lead with the contaminant stack (specific > generic "well water problems").
- Form prefilled `well water treatment`; well buyers often call — keep phone prominent.

### Copy — Hero
> **Eyebrow:** Loxahatchee · The Acreage · Wellington
> **H1:** Well Water Treatment for Western Palm Beach County
> **Sub:** If you're on a private well, no utility is treating your water — you are. We run a full
> well panel for iron, sulfur, bacteria, nitrates, and hardness, then build the treatment your
> water actually needs.
> **Primary CTA:** Book a Free Well-Water Test · **Secondary:** Call (561) 555-0100

### Copy — Problem block
> **H2:** What's really in your well
> Western Palm Beach County wells pull from shallow zones loaded with more than hardness. The
> usual suspects: **iron** (orange stains on fixtures and laundry), **hydrogen sulfide** (the
> rotten-egg smell), **bacteria** (wells aren't chlorinated like city water), **nitrates**, and
> **hardness** on top of all of it. A softener alone won't fix a well — it'll clog on the iron. You
> need the right stages in the right order, and that starts with knowing what's actually there.

### Copy — Why-Test block (well angle — the regulatory wedge)
> **H2:** Nobody's testing your well but you
> Federal PFAS drinking-water limits — the 4-ppt standard you've seen in the news — apply only to
> public water systems. Private wells are excluded entirely. More than 43 million Americans on
> wells have no required testing or treatment of any kind. That's not a gap the county fills; it's
> yours to close. We test first so you treat what your water has, not what a brochure assumes.
> **Chips:** Iron · Hydrogen sulfide · Bacteria · Nitrates · Hardness 15–22 GPG · PFAS

### Copy — Solution block
> **H2:** A treatment train, not a single box
> Well water needs stages. We typically pre-treat iron and sulfur first (so they don't foul
> everything downstream), then soften the hardness, then polish with filtration or reverse osmosis
> for drinking water. The exact train depends on your test — some wells need every stage, some need
> two. We design it around your numbers.

### Copy — Process block (steps)
> Comprehensive well-water test — iron, sulfur, bacteria, nitrates, hardness.
> Custom treatment design — only the stages your water actually needs.
> Professional install — sequenced correctly so nothing fouls downstream.
> Follow-up verification — we retest after install to confirm it's working.

### Copy — Price band
> **Heading:** What well-water treatment costs in Palm Beach County
> - Complete well system with iron pre-treatment — **$3,500–$6,500 installed**
> - Softener + filter + RO polishing — **added per test results**
> **Disclaimer:** Well systems are scoped from your test — no two wells are identical, and we won't
> quote one blind.

### Copy — FAQ
> **Q: Why does my well water smell like rotten eggs?**
> That's hydrogen sulfide gas, common in western PBC wells. It's treatable — usually with an
> oxidizing filter stage ahead of your softener. The test confirms the level and the right method.
> **Q: Will a water softener fix my well water?**
> Not by itself. Softeners remove hardness but clog on iron and don't touch sulfur or bacteria. A
> well needs a multi-stage system, sized from a full test.
> **Q: Do I need to test my well if the water looks fine?**
> Yes. Bacteria, nitrates, and low-level iron are invisible. Private wells have no mandated testing,
> so a clear glass tells you nothing about what's dissolved in it.
> **Q: How often should well water be tested?**
> At minimum annually, and after any change in taste, smell, or color — or after major storms that
> can affect shallow wells.

### Copy — Service area
> **Heading:** Serving western Palm Beach County wells
> Cities: Loxahatchee · The Acreage · Wellington · Royal Palm Beach · Westlake · Belle Glade
> **Note:** Equestrian and acreage properties west of the Turnpike are our specialty — that's where
> well water and iron pre-treatment matter most.

================================================================================
## 3. WHOLE-HOUSE FILTRATION PAGE   → /whole-house-filtration
================================================================================

**Primary keyword:** `whole house water filter palm beach`
**Support:** `chlorine filter home`, `pfas water filter palm beach`, `carbon water filter [city]`,
`reverse osmosis system [city]` (RO gets its own page later; cross-link)
**Page goal:** Book a free water test → filtration quote. **Primary conversion:** form; call secondary.
**Buyer:** city-water homeowner concerned about chlorine taste/smell, PFAS, or overall water quality
(not primarily hardness — that's the softener page; cross-link the two).

### Storyblok block order
`hero(standard)` → `service_block(problem)` → `why_test(contaminant focus)` →
`service_block(solution)` → `price_band` → `faq` → `testimonial_row` → `cta_band`

### Wireframe
```
┌───────────────────────────────────────────────┐
│ STICKY: logo · nav · [Call (561)...]           │
├───────────────────────────────────────────────┤
│ HERO (standard)                                 │
│  eyebrow: Palm Beach County · Whole-House Filters│
│  H1: Whole-House Water Filtration in Palm Beach  │
│      County                                      │
│  sub: Chlorine, sediment & PFAS reduction at the │
│       point where water enters your home.        │
│  [Book a Free Water Test] [Call]                 │
├───────────────────────────────────────────────┤
│ PROBLEM: chlorine taste/smell · PFAS concern ·   │
│  sediment · what filtration does vs softening    │
├───────────────────────────────────────────────┤
│ WHY TEST: PFAS status + what a filter removes     │
├───────────────────────────────────────────────┤
│ SOLUTION: point-of-entry carbon + stages; RO      │
│  for drinking (cross-link RO page)                │
├───────────────────────────────────────────────┤
│ PRICE BAND: filtration from $2,500; combos        │
├───────────────────────────────────────────────┤
│ FAQ (schema) → REVIEWS → CTA → FOOTER             │
└───────────────────────────────────────────────┘
```

### CTA placement
Hero; sticky call; CTA band after reviews. Cross-link softener + RO pages inline (not competing —
complementary; internal linking helps SEO).

### Trust elements
License #, insured, free test, clear "filter vs softener" honesty (builds trust by not overselling),
EPA-recognized media (activated carbon / anion exchange / RO for PFAS).

### SEO notes
- Title: `Whole-House Water Filtration in Palm Beach County | What's in Your Water`
- Distinct primary keyword from the softener page — do NOT let these two cannibalize. Filtration =
  contaminants/taste; softener = hardness. Cross-link, don't overlap keywords.
- Schema: Service + LocalBusiness + FAQPage.
- PFAS content: accurate, current (4 ppt MCL for public systems intact; treatment = GAC/anion/RO).

### Conversion notes
- The "filter vs softener" explainer prevents mis-sold leads and captures both intents cleanly.
- Cross-link RO page for drinking-water buyers (upsell path).
- Form prefilled `whole_house_filter`.

### Copy — Hero
> **Eyebrow:** Palm Beach County · Whole-House Filtration
> **H1:** Whole-House Water Filtration in Palm Beach County
> **Sub:** Reduce chlorine, sediment, and contaminants like PFAS at your home's point of entry — so
> every tap, shower, and appliance gets cleaner water.
> **Primary CTA:** Book a Free Water Test · **Secondary:** Call (561) 555-0100

### Copy — Problem block
> **H2:** Filtration vs softening — what each actually does
> A softener removes hardness. A filter removes contaminants — chlorine and chloramine (the taste
> and smell), sediment, and reduces chemicals like PFAS. They solve different problems, and many
> homes want both. We'll tell you honestly which your water needs, based on the test, instead of
> selling you the bigger package by default.

### Copy — Why-Test block (contaminant focus)
> **H2:** What's in Palm Beach County tap water
> Municipal water here is treated and safe to federal standards, but "meets the standard" isn't the
> same as "nothing in it." Chlorine and chloramine are added for disinfection and carry through to
> your tap. PFAS — "forever chemicals" — are federally limited to 4 parts per trillion for public
> systems, with utilities on a compliance timeline running to 2031. A point-of-entry carbon filter
> reduces chlorine taste and odor; for PFAS specifically, activated carbon, anion exchange, and
> reverse osmosis are the EPA-recognized treatments. We test, then match the media to what's there.
> **Chips:** Chlorine · Chloramine · Sediment · PFAS · Taste & odor

### Copy — Solution block
> **H2:** Point-of-entry filtration, sized to your home
> A whole-house filter installs where water enters, so every fixture benefits. We spec the carbon
> and stages to your flow rate and contaminant profile. For drinking and cooking, we usually add a
> reverse-osmosis unit at the kitchen sink — the final polish for the water you actually consume.
> (See our reverse osmosis page for that stage.)

### Copy — Price band
> **Heading:** What whole-house filtration costs
> - Whole-house filtration — **from $2,500 installed**
> - Softener + filter combo — **from $2,500** (covers hardness + contaminants)
> - Add under-sink RO — **priced per system**
> **Disclaimer:** Final scope after a free in-home test. We spec media to your water, not a catalog.

### Copy — FAQ
> **Q: Does a whole-house filter remove PFAS?**
> Activated carbon and anion exchange reduce PFAS, and reverse osmosis removes it most completely.
> We select the media based on your test — a standard sediment filter won't do it.
> **Q: Do I need a filter if I have a softener?**
> They do different jobs. A softener handles hardness; a filter handles chlorine, taste, and
> contaminants. Many PBC homes run both — often as a single combined system.
> **Q: Will filtration fix the chlorine smell?**
> Yes. A carbon stage removes chlorine and chloramine, which is what causes the pool-like taste and
> smell at the tap.

================================================================================
## 4. WATER HEATER PAGE   → /water-heater
================================================================================

**Primary keyword:** `water heater repair palm beach county` (H2 target: `tankless water heater [city]`)
**Support:** `water heater replacement [city]`, `tankless water heater worth it florida`,
`no hot water [city]`, `water heater installation`
**Page goal:** Book repair/replacement or tankless quote. **Primary conversion:** call (heater
failures are urgent) → form secondary. Note the tie-in: hard water kills heaters, cross-link softener.
**Buyer:** homeowner with a failing/failed heater (urgent) OR planning a tankless upgrade (considered).

### Storyblok block order
`hero(standard)` → `service_block(problem)` → `service_block(solution)` → `price_band` →
`service_block(process)` → `faq` → `testimonial_row` → `cta_band`

### Wireframe
```
┌───────────────────────────────────────────────┐
│ STICKY: logo · nav · [Call (561)...]           │
├───────────────────────────────────────────────┤
│ HERO (standard, call-leaning)                    │
│  eyebrow: Palm Beach County · Water Heaters      │
│  H1: Water Heater Repair & Replacement in Palm   │
│      Beach County                                │
│  sub: Repair, replace, or upgrade to tankless —  │
│       same-day service when the hot water's out. │
│  [Call Now] [Book a Visit]  ← call primary here  │
├───────────────────────────────────────────────┤
│ PROBLEM: no hot water · leaking tank · rusty      │
│  water · pilot won't stay lit · age/scale         │
├───────────────────────────────────────────────┤
│ SOLUTION: repair vs replace vs tankless;          │
│  hard-water link (cross-link softener page)       │
├───────────────────────────────────────────────┤
│ PRICE BAND: repair / tank replace / tankless      │
├───────────────────────────────────────────────┤
│ PROCESS: diagnose → quote → same-day fix/install  │
├───────────────────────────────────────────────┤
│ FAQ (schema) → REVIEWS → CTA → FOOTER             │
└───────────────────────────────────────────────┘
```

### CTA placement
Call primary in hero (urgency); sticky call; book-a-visit secondary for planned upgrades. CTA band
after reviews. This page leans phone-first more than softener/filtration because failures are urgent.

### Trust elements
License #, insured, same-day service, upfront flat-rate pricing, brands installed (Bradford White/
Rheem/AO Smith — match competitors), 1-yr parts+labor warranty.

### SEO notes
- Title: `Water Heater Repair & Replacement in Palm Beach County | What's in Your Water`
- Primary keyword in H1; `tankless water heater` as a strong H2 (own the upgrade intent).
- Schema: Service + LocalBusiness + FAQPage.
- Hard-water/scale angle links back to the softener page — genuine internal-linking win, and true:
  scale from 15–22 GPG water shortens heater life. Cross-link both directions.

### Conversion notes
- Split the buyer: urgent (call now, "no hot water") vs planned (tankless research → book visit).
- Repair-vs-replace honesty builds trust and captures both.
- Form prefilled `water_heater`; emergency-flavored heater failures can set `urgency=emergency`.

### Copy — Hero
> **Eyebrow:** Palm Beach County · Water Heaters
> **H1:** Water Heater Repair & Replacement in Palm Beach County
> **Sub:** No hot water, a leaking tank, or rusty water? We diagnose fast and fix same-day — and if
> it's time to replace, we'll walk you through tank vs tankless with upfront pricing.
> **Primary CTA:** Call (561) 555-0100 · **Secondary:** Book a Visit

### Copy — Problem block
> **H2:** Signs your water heater is failing
> No hot water or it runs out fast. Water pooling around the base — a leaking tank can't be repaired,
> only replaced. Rusty or metallic-smelling hot water. A pilot that won't stay lit. Popping or
> rumbling from sediment. Most tank heaters last 8–12 years here, and hard water shortens that: scale
> from 15–22 GPG water bakes onto the elements and eats years off the tank. (A softener protects a
> new heater — see our water softener page.)

### Copy — Solution block
> **H2:** Repair, replace, or go tankless
> If it's a valve, thermostat, or element, we repair it — no reason to replace a good tank. If it's
> leaking or past its life, we replace it, usually same-day. And if you're upgrading, tankless makes
> sense for a lot of Florida homes: endless hot water, smaller footprint, longer lifespan — though it
> costs more up front and, in our hard water, runs best with a softener ahead of it. We'll give you
> the honest tradeoff for your home, not a one-size push.

### Copy — Price band
> **Heading:** Water heater pricing in Palm Beach County
> - Repair (valve, thermostat, element) — **flat-rate, quoted on site**
> - Tank replacement — **priced by size & brand, upfront**
> - Tankless conversion — **quoted after a quick home assessment**
> **Disclaimer:** Flat-rate pricing shown before any work begins. No surprise add-ons.

### Copy — Process block (steps)
> Fast diagnosis — we find the cause, not just the symptom.
> Upfront flat-rate quote — you approve the price before we start.
> Same-day repair or replacement — most jobs done in one visit.
> Warranty-backed — 1 year on parts and labor.

### Copy — FAQ
> **Q: Is it worth repairing my water heater or should I replace it?**
> If the tank is leaking or over ~10 years old, replacement usually makes more sense. Valve,
> thermostat, and element failures are worth repairing. We tell you honestly on site.
> **Q: Is a tankless water heater worth it in Florida?**
> For many homes, yes — endless hot water, longer life, less space. It costs more up front and runs
> best with a softener ahead of it, since our hard water scales tankless units fastest. We'll size
> the tradeoff to your usage.
> **Q: Why is my hot water rusty?**
> Usually a corroding tank or a spent anode rod. If it's only the hot side, it's the heater — often
> a sign it's near the end of its life.
> **Q: How long does a water heater last here?**
> Tank heaters typically last 8–12 years in Palm Beach County; hard water shortens that. Softened
> water and annual flushing extend it.

================================================================================
## Cross-linking map (internal SEO)
================================================================================
- Softener  ⇄ Filtration (hardness vs contaminants — complementary)
- Softener  ⇄ Water Heater (hard water kills heaters — both directions)
- Filtration → RO page (drinking-water polish upsell)
- Well Water → Softener + Filtration (well train includes both stages)
- Every service page → Contact + Reviews + Service Area
- Homepage service grid → all four pages
