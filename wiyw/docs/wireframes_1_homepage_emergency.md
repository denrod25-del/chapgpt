# WiYW — Page Wireframes & Copy Outlines

Brand: **What's in Your Water** · Palm Beach County · water treatment + full plumbing.
Positioning note: WiYW leads with **water quality** (the differentiator) but must capture
**plumbing + emergency** demand too. Homepage balances both; emergency page is plumbing-first.

---

## HOMEPAGE

**Page goal:** Route visitors to (a) call now, (b) book a water test, or (c) enter a service page.
**Primary conversion:** phone call. **Secondary:** water-test lead form.

### Wireframe (top → bottom)

```
┌─────────────────────────────────────────────┐
│ STICKY HEADER: logo · nav · [Call (561)...]  │ ← phone always visible
├─────────────────────────────────────────────┤
│ HERO                                         │
│  H1: Know What's in Your Water.              │
│      Palm Beach County's Water & Plumbing Pro│
│  Sub: Water testing, softeners, filtration,  │
│       water heaters & full plumbing.         │
│  [Book a Free Water Test]  [Call Now]        │
│  trust strip: Licensed · Insured · 5.0 ★     │
├─────────────────────────────────────────────┤
│ SERVICES GRID (6 cards)                      │
│  Water Treatment · Softeners · Whole-House   │
│  Filtration · Water Heaters · Drains · Repipe│
├─────────────────────────────────────────────┤
│ "WHY TEST YOUR WATER" (WiYW differentiator)  │
│  hardness · iron · chlorine · PFAS icons     │
├─────────────────────────────────────────────┤
│ REVIEWS (3 featured, Google ★)               │
├─────────────────────────────────────────────┤
│ SERVICE AREA map (PBC + well-water pockets)  │
├─────────────────────────────────────────────┤
│ LEAD FORM: name · phone · service · [Submit] │
├─────────────────────────────────────────────┤
│ FOOTER: NAP · license # · hours · socials    │
└─────────────────────────────────────────────┘
```

### CTA placement
- Sticky header phone (visible 100% of scroll)
- Hero dual CTA (test = primary teal button, call = secondary)
- Repeat call CTA after reviews (trust peak)
- Form near footer as low-intent catch

### Trust elements
License #, insured badge, Google rating, years serving PBC, brand-consistent water-quality iconography.

### SEO notes
- Title: `Water Treatment & Plumbing in Palm Beach County | What's in Your Water`
- H1 contains "Water" + "Palm Beach County" + plumbing breadth
- LocalBusiness + Service schema; NAP in footer matches GBP exactly
- Internal links to all 6 service pages

### Conversion notes
- Phone above the fold, tel: link fires `call_clicked` event
- Form posts to `POST /leads` with `source=website`, `landing_page=/`
- Keep form to 3 fields (name, phone, service_type) — every extra field drops completion

### Copy — Hero
> **H1:** Know What's in Your Water.
> **Subhead:** From hard water and iron to PFAS and chlorine — plus water heaters, drains, and full plumbing. Palm Beach County's licensed water & plumbing specialists.
> **Primary CTA:** Book a Free Water Test
> **Secondary CTA:** Call (561) XXX-XXXX

### Copy — "Why Test" section
> Palm Beach County water isn't the same street to street. Coastal homes fight hardness and chlorine; well homes out west deal with iron, sulfur, and bacteria. We test first, then fix what's actually there — no guesswork, no overselling.

---

## EMERGENCY PLUMBING PAGE

**Page goal:** One action — call now. Everything else is friction.
**Primary conversion:** phone call (emergency leads convert on the phone, not forms).

### Wireframe

```
┌─────────────────────────────────────────────┐
│ STICKY: logo · [🔴 CALL NOW (561)...]        │
├─────────────────────────────────────────────┤
│ HERO (urgent, high contrast)                 │
│  H1: Plumbing Emergency in Palm Beach County?│
│  Sub: Burst pipe. No hot water. Sewage backup│
│       We answer 24/7 and get there fast.     │
│  [🔴 CALL NOW — big]                          │
│  "Answered 24/7 · Licensed · Upfront pricing"│
├─────────────────────────────────────────────┤
│ WHAT WE HANDLE (fast scan list)              │
│  Burst/leaking pipes · Water heater failure  │
│  Sewage backup · Overflowing/clogged drains  │
│  Flooding · Post-storm plumbing              │
├─────────────────────────────────────────────┤
│ RESPONSE PROMISE + optional emergency form   │
│  (form only as fallback if they won't call)  │
├─────────────────────────────────────────────┤
│ REVIEWS (2, emergency-specific)              │
├─────────────────────────────────────────────┤
│ SERVICE AREA + FOOTER NAP                    │
└─────────────────────────────────────────────┘
```

### CTA placement
- Giant call button in hero (largest element on page)
- Sticky call button entire scroll
- Emergency form ONLY as fallback, below the fold — minimal fields, flagged `urgency=emergency`

### Trust elements
"Answered 24/7" (only if true), licensed/insured, upfront pricing, real emergency reviews.

### SEO notes
- Title: `24/7 Emergency Plumber in Palm Beach County | What's in Your Water`
- H1: `emergency plumber [city]` intent
- Schema: Service + LocalBusiness, `availableChannel` phone
- Target queries: emergency plumber wpb, burst pipe repair boca, 24 hour plumber delray

### Conversion notes
- Minimize everything above the call button — no nav distractions
- tel: link → `call_clicked` event with `{page:'emergency'}`
- If form used: posts to `/leads` with `urgency=emergency` → fires Automation #8
  (instant owner alert + 5-min promise SMS), skips nurture
- Page load fires `service_page_viewed` with `{service_type:'emergency'}`

### Copy — Hero
> **H1:** Plumbing Emergency in Palm Beach County?
> **Subhead:** Burst pipe, no hot water, sewage backup, or storm flooding — we answer 24/7 and get to your door fast. Licensed, insured, and upfront about pricing before we start.
> **CTA:** 🔴 CALL NOW — (561) XXX-XXXX

### Copy — Response promise
> Call and you'll talk to a real person, not an answering service. We'll confirm we're on the way and give you a clear arrival window. No surprise fees — you approve the price before any work begins.

### Copy — Emergency form fallback
> Can't talk right now? Send your number and we'll call you within 5 minutes.
> [Name] [Phone] [What's happening?] → **Request Emergency Callback**
