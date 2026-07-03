# SECTION 16 — Naming Conventions

One table to rule the stack. These match the shipped code, migrations, n8n JSONs, and
`docs/BREVO_SETUP.md` — deviations are bugs.

| Object | Pattern | Examples |
|---|---|---|
| **Events** | `snake_case`, past tense, `<object>_<verb>`; page views `<page>_viewed`; CHECK-enforced in migration 005 | `form_submitted`, `sms_delivered`, `emergency_service_page_viewed` |
| **Tags** | `kebab-case`, noun or state, pre-seeded in `tags` | `lead-new`, `quote-pending`, `well-water`, `reactivation-warm` |
| **Campaign names** | `<channel>_<purpose>_<city>_<yyyymm>` (UNIQUE in `campaigns`) | `email_reactivation_wpb_202607`, `sms_seasonal_lox_202608` |
| **City codes** | short lowercase, from `service_areas.city_code` | `wpb`, `boca`, `lox`, `acreage`, `pbg` |
| **Brevo lists** | `list_<descriptor>` | `list_leads`, `list_customers`, `list_reactivation` |
| **Brevo segments** | `seg_<descriptor>` | `seg_well_water`, `seg_lapsed_9mo` |
| **Brevo attributes** | `UPPER_SNAKE` | `WATER_SOURCE`, `LIFETIME_VALUE` |
| **Brevo automations** | `wf_<descriptor>` | `wf_quote_followup` |
| **Email templates (transactional)** | `txn_<purpose>` | `txn_lead_confirmation`, `txn_invoice` |
| **Email templates (marketing)** | `mkt_<purpose>` | `mkt_reactivation_offer` |
| **SMS templates** | `sms_<purpose>[_<variant>]` | `sms_reminder_24h`, `sms_review`, `sms_owner_alert` |
| **Webhook event types** | provider-native names stored verbatim in `webhooks_inbox.event_type`; canonical mapping happens at processing into taxonomy events | Brevo `opened` → event `email_opened` |
| **n8n workflow names** | `wf<N>_<purpose>` (file: `wf<N>_<purpose>.json`); `workflow_key` in `automation_runs` = same string | `wf1_appointment_reminders`, `wf4_missed_lead_recovery` |
| **DB tables** | `snake_case`, plural | `communication_logs`, `entity_tags` |
| **DB indexes** | `idx_<table>_<purpose>`; unique `uq_<table>_<purpose>` | `idx_leads_missed`, `uq_reviews_dedupe` |
| **DB triggers/functions** | `trg_<table>_<purpose>` / verb phrase | `trg_job_completed`, `touch_updated_at()` |
| **Migrations** | `NNN_<topic>.sql` + `NNN_<topic>.down.sql`, applied in order | `005_platform_entities.sql` |
| **FastAPI modules** | `snake_case` by domain: routers `routers/<domain>.py`, services `services/<provider-or-flow>.py`, schemas `schemas/<domain>.py` | `routers/leads.py`, `services/brevo.py` |
| **Routes** | plural nouns, kebab-case path segments, verbs only for action sub-resources | `/api/v1/quote-requests`, `/api/v1/reviews/request` |
| **Env vars** | `UPPER_SNAKE`, provider-prefixed | `GATEWAYAPI_WEBHOOK_SECRET` |
| **Brand slugs** | short lowercase | `wiyw` |

Cross-system invariant: the **template key** (`sms_reminder_24h`) is the join key between
`communication_logs.template`, n8n node config, and this doc — never send a message without one.
