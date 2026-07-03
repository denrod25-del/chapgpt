# WiYW — Brevo Implementation Checklist & Naming Conventions

Brevo is the **marketing communications source of truth** (segments, campaigns, nurture).
It is NOT used for transactional receipts (those are Resend/GatewayAPI). Contacts are mirrored
from Postgres, which remains the system of record.

---

## Phase 0 — Account & Deliverability (do first, manual)

- [ ] Verify sending domain `mail.whatsinyourwater.com` (separate subdomain from transactional)
- [ ] Add SPF record
- [ ] Add DKIM record
- [ ] Add DMARC record (`p=quarantine` to start, tighten to `reject` after 2 weeks clean)
- [ ] Confirm domain shows "Authenticated" in Brevo → Senders & Domains
- [ ] Set a recognizable sender name: `What's in Your Water`
- [ ] Generate API key (Settings → SMTP & API) → store as `BREVO_API_KEY`
- [ ] Configure a webhook (Settings → Webhooks) → POST opens/clicks/unsubscribes to `/webhooks/brevo`

**Success criteria:** test email lands in Gmail Primary inbox, not Promotions/Spam.

---

## Lists (static membership)

| List ID | Name | Purpose |
|---------|------|---------|
| 1 | `list_all_contacts` | master list, every contact |
| 2 | `list_leads` | new leads not yet customers |
| 3 | `list_customers` | converted, has ≥1 job |
| 4 | `list_reactivation` | lapsed >9 months |

> The backend upserts leads into **list 2**. On first job completion, move to **list 3**.

---

## Segments (dynamic — auto-membership by attribute)

| Segment name | Rule |
|--------------|------|
| `seg_emergency_leads` | tag = emergency |
| `seg_quote_pending` | tag = quote-pending |
| `seg_review_requested` | tag = review-requested |
| `seg_lapsed_9mo` | LAST_JOB_AT < today − 9 months |
| `seg_high_value` | LIFETIME_VALUE > 3000 |
| `seg_well_water` | WATER_SOURCE = well |
| `seg_city_water` | WATER_SOURCE = city |

> `seg_well_water` matters for WiYW: well-water homes need different messaging
> (iron/sulfur/bacteria, no municipal chlorine) than city-water homes (chlorine/hardness/PFAS).

---

## Custom Attributes

| Attribute | Type | Source |
|-----------|------|--------|
| `SERVICE_TYPE` | text | lead.service_type |
| `URGENCY` | text | lead.urgency |
| `SOURCE` | text | lead.source |
| `WATER_SOURCE` | text | lead.water_source |
| `CITY` | text | lead.city |
| `POSTAL_CODE` | text | lead.postal_code |
| `LIFETIME_VALUE` | number | customer.lifetime_value |
| `LAST_JOB_AT` | date | customer.last_job_at |
| `CONSENT_SMS` | boolean | customer.consent_sms |
| `STATUS` | text | lead.status |

---

## Campaign Folder Structure

```
Transactional-Backup/     (failover only; primary is Resend)
Nurture-Quote/
Reviews/
Reactivation/
Seasonal-Offers/          (FL: pre-hurricane prep, dry-season water quality)
Education/                (water-quality content — WiYW's brand differentiator)
```

---

## Automation Workflows (Brevo-native)

| Workflow | Entry trigger | Notes |
|----------|---------------|-------|
| `wf_welcome` | contact added to list_leads | 3-email intro |
| `wf_quote_followup` | tag quote-pending added | Day 0/2/5 |
| `wf_review_request` | (backend-triggered email leg only) | SMS leg is GatewayAPI |
| `wf_reactivation_9mo` | added to list_reactivation | paired with n8n WF-3 |

> Division of labor: **timing-critical / SMS** legs run in FastAPI + n8n against Postgres.
> **Email nurture sequences** run natively in Brevo. Don't rebuild the same sequence in both.

---

## Example: Welcome Sequence (`wf_welcome`)

1. **Day 0** — "Thanks for reaching out — here's what happens next" + what WiYW tests for
2. **Day 2** — "Why Palm Beach County homeowners test their water" (hardness, iron, PFAS, chlorine)
3. **Day 5** — "Common water problems we fix fast" + soft CTA to book a water test

## Example: Review Request Sequence (`wf_review_request`, email leg)

1. **+2h** — (SMS, GatewayAPI, not Brevo)
2. **+3d** — Email "How did we do?" with Google review link
3. **+7d** — Final gentle nudge, only if no review_received event

---

## Naming Conventions (canonical — matches Postgres + FastAPI)

| Object | Pattern | Example |
|--------|---------|---------|
| Campaign | `<channel>_<purpose>_<city>_<yyyymm>` | `email_reactivation_wpb_202607` |
| Tag | `kebab-case` | `well-water`, `quote-pending` |
| Segment | `seg_<descriptor>` | `seg_lapsed_9mo` |
| List | `list_<descriptor>` | `list_customers` |
| Workflow | `wf_<descriptor>` | `wf_review_request` |
| Attribute | `UPPER_SNAKE` | `WATER_SOURCE` |
| Template (txn) | `txn_<purpose>` | `txn_lead_confirmation` |
| Template (sms) | `sms_<purpose>` | `sms_reminder_24h` |

Cities in campaign names use short codes: `wpb` (West Palm Beach), `boca`, `delray`,
`boynton`, `jupiter`, `pbg` (Palm Beach Gardens), `acreage`, `lox` (Loxahatchee), `glades`.

---

## Reporting Dashboard Checklist (review weekly)

- [ ] Open rate by campaign
- [ ] Click rate by campaign
- [ ] Unsubscribe rate (flag if > 0.5%)
- [ ] Bounce rate (flag if > 2%)
- [ ] Automation completion % per workflow
- [ ] Review-request → review_received conversion
- [ ] Reactivation → booking count
- [ ] Segment growth: seg_well_water vs seg_city_water
