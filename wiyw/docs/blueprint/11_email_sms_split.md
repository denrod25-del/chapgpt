# SECTION 11 — Email & SMS Responsibility Split

Canonical rules live in `docs/OWNERSHIP.md`. Summary: **campaign/list/sequence → Brevo;
1:1 system message → Resend (Mailgun failover on non-2xx only); every SMS → GatewayAPI.**
Mailgun additionally owns inbound email parse on the `mg.` subdomain. Never cross.

## Decision table

| Message | Provider | Template key | Notes |
|---|---|---|---|
| Marketing campaign email (offers, education, seasonal) | **Brevo** | `mkt_*` | lists/segments per BREVO_SETUP; campaign row in Postgres for the record |
| Nurture/drip sequence (welcome, quote follow-up) | **Brevo** | `mkt_*` via `wf_*` | Brevo-native automations |
| Transactional confirmation email (lead/booking) | **Resend** → Mailgun failover | `txn_lead_confirmation`, `txn_booking_confirmation` | shipped in `services/email.py` |
| Invoice email | **Resend** → Mailgun failover | `txn_invoice` | money-path = transactional, never Brevo |
| Password reset (future portal) | **Resend** → Mailgun failover | `txn_password_reset` | highest deliverability requirement |
| Review request — initial email leg | **Resend** | `txn_review_request` | fires once per job |
| Review request — delayed nurture leg (+3d, +7d) | **Brevo** | `wf_review_request` | only if no `review_received` event |
| Review request SMS | **GatewayAPI** | `sms_review` | primary leg when `consent_sms` |
| Appointment reminder SMS (24h / 2h) | **GatewayAPI** | `sms_reminder_24h`, `sms_reminder_2h` | n8n WF-1; email fallback via Resend if SMS fails |
| Emergency lead acknowledgement SMS | **GatewayAPI** | `sms_emergency_ack` | in-request in `POST /leads` — must fire in seconds |
| Owner alerts (new lead, emergency, missed lead) | **GatewayAPI** | `sms_owner_alert` | Resend email fallback if GatewayAPI down |
| Inbound email (replies to transactional) | **Mailgun** inbound route | — | parsed → comm log inbound + owner notification |

## Domain strategy

| Purpose | Domain | Provider |
|---|---|---|
| Transactional | `mail.whatsinyourwater.com` | Resend (SPF/DKIM/DMARC) |
| Failover + inbound | `mg.whatsinyourwater.com` | Mailgun |
| Marketing | separate Brevo-verified sender on `mail.` or dedicated `news.` subdomain | Brevo |

Separate subdomains isolate reputations: a marketing spam complaint can't hurt invoice
deliverability.

## Failover semantics (shipped behavior, keep)

`send_confirmation()` tries Resend; any exception or non-2xx → Mailgun with identical content;
both fail → `log.error`, flow continues (SMS is the redundant channel). Failover is **inside
the email service** — callers and n8n never choose Mailgun explicitly, which is why there is no
`/integrations/mailgun/send-email` route.
