# Event Taxonomy

*(Mirrors blueprint section 9 — keep the two in sync when the taxonomy migration changes.)*

Canonical, CHECK-enforced in `events.event_name` (migration 005 — the DB rejects names not
listed there; extending the taxonomy = new migration swapping the constraint). All events are
append-only rows in `events` with `payload JSONB`, optional `lead_id`/`customer_id`,
`source_system`, `brand_id`.

Naming rules: `snake_case`, past tense, `<object>_<verb>` (`form_submitted`, `sms_delivered`);
page views are `<page>_viewed`. No `.`/`:` namespacing — flat names match the CHECK constraint
and n8n SQL cleanly.

## Catalog

| Event | Producer | Consumers | Payload fields (beyond ids) |
|---|---|---|---|
| `page_viewed` | frontend | dashboard, attribution | `path`, `referrer`, `anonymous_id` |
| `landing_page_viewed` | frontend | attribution (campaign entry) | `path`, `utm_*`, `anonymous_id` |
| `service_page_viewed` | frontend | dashboard, SEO | `path`, `service_type` |
| `emergency_service_page_viewed` | frontend | dashboard (demand signal) | `path` |
| `financing_page_viewed` | frontend | sales follow-up context | `path` |
| `coupon_viewed` | frontend | campaign measurement | `coupon_code`, `path` |
| `call_clicked` | frontend | dashboard (call attribution) | `path`, `phone_shown` |
| `form_started` | frontend | funnel drop-off analysis | `form_id`, `path` |
| `form_submitted` | backend (`/leads`) ✅ | n8n WF-4, dashboard | full lead payload |
| `lead_created` | backend | Brevo mirror, dashboard | `lead_id`, `service_type`, `urgency`, `source` |
| `quote_requested` | backend (`/quotes`) ✅ | Brevo `wf_quote_followup`, dashboard | `service_type` |
| `booking_requested` | backend/frontend | ops | `requested_for`, `service_type` |
| `appointment_booked` | backend (`/bookings`) ✅ | WF-1 reminder eligibility, dashboard | `booking_id`, `scheduled_for` |
| `booking_confirmed` | backend (customer replied C / PATCH) | dashboard, no-show analysis | `booking_id` |
| `appointment_reminder_scheduled` | n8n WF-1 | audit | `booking_id`, `window` (`24h`/`2h`) |
| `appointment_reminder_sent` | n8n WF-1 ✅ | no-show analysis | `booking_id`, `channel`, `window` |
| `job_completed` | backend (`/jobs/{id}/complete`) ✅ | WF-2 review flow, LTV (DB trigger) | `job_id`, `amount` |
| `invoice_sent` | backend (future invoicing) | dashboard | `job_id`, `amount` |
| `review_request_sent` | n8n WF-2 / `POST /reviews/request` ✅ | conversion tracking, WF-2b nudge guard | `job_id`, `channel` |
| `review_received` | backend (`/reviews`) / WF-5 ✅ | dashboard, WF-2b stop signal | `rating`, `platform` |
| `email_sent` | backend send path | delivery-rate calc | `template`, `provider`, `provider_msg_id` |
| `email_delivered` | Brevo/Resend/Mailgun webhooks | delivery-rate calc | `provider_msg_id` |
| `email_opened` | Brevo/Resend webhooks ✅ | WF-3 engagement branch | `email`, `campaign` |
| `email_clicked` | Brevo/Resend webhooks ✅ | WF-3 warm-tagging | `email`, `url` |
| `sms_sent` | backend send path | delivery-rate calc | `template`, `provider_msg_id` |
| `sms_delivered` | GatewayAPI DLR webhook | delivery-rate calc | `provider_msg_id` |
| `sms_clicked` | shortlink redirect ✅ | review-link conversion | `link_id`, `job_id` |
| `contact_unsubscribed` | Brevo/GatewayAPI webhooks | consent audit trail | `email`/`phone`, `channel` |

✅ = producer already wired in shipped code/workflows.

## Sample payloads

```json
{"event_name": "form_submitted", "lead_id": "558164f4-…", "source_system": "backend",
 "payload": {"full_name": "Maria Gonzalez", "phone": "+15615550142", "service_type": "water_softener",
             "urgency": "standard", "water_source": "well", "source": "website", "city": "Loxahatchee"}}
```
```json
{"event_name": "appointment_reminder_sent", "customer_id": "9a2f…", "source_system": "n8n",
 "payload": {"booking_id": "b7c1…", "channel": "sms", "window": "24h"}}
```
```json
{"event_name": "call_clicked", "source_system": "frontend",
 "payload": {"path": "/emergency-plumber", "phone_shown": "+15615550100", "anonymous_id": "anon_8f3k2"}}
```

## Retention

| Class | Events | Retention |
|---|---|---|
| High-volume page/funnel | `page_viewed`, `*_page_viewed`, `form_started`, `coupon_viewed` | 13 months (YoY comparison), then aggregate to monthly counts + delete rows |
| Delivery receipts | `email_sent/delivered`, `sms_sent/delivered` | 6 months (comm_logs keeps the per-message record) |
| Business lifecycle | `form_submitted` … `job_completed`, `review_*`, `booking_*` | indefinite — this *is* the business history |
| Consent | `contact_unsubscribed` | indefinite (compliance evidence) |

Implement retention as a monthly n8n job:
`DELETE FROM events WHERE event_name = ANY($1) AND created_at < now() - interval '13 months'`
(bounded batches of 10k). No partitioning until the table passes ~10M rows.
