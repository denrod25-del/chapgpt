# n8n Workflow Variables

All workflows read configuration through `$env.*` expressions. Set these as
n8n Variables (Settings → Variables) or as process environment variables on
the n8n host, then restart/reload n8n.

| Variable | Example | Used where |
|---|---|---|
| `API_BASE_URL` | `https://api.acmeplumbing.example` | Every HTTP Request node that calls FastAPI (all 8 workflows). No trailing slash. |
| `INTERNAL_API_TOKEN` | `openssl rand -hex 32` output | `Authorization: Bearer …` header on every FastAPI call. Must match the backend's `INTERNAL_API_TOKEN`. |
| `BREVO_API_KEY` | `xkeysib-…` | **Reserved.** Not used by default — Brevo sync goes through `POST /api/v1/integrations/brevo/sync-contact`. Needed only if you rewire a node to call Brevo directly (Header Auth `api-key`). |
| `BREVO_BASE_URL` | `https://api.brevo.com/v3` | **Reserved.** Same as above. |
| `GATEWAYAPI_API_TOKEN` | GatewayAPI token | **Reserved.** SMS goes through `POST /api/v1/integrations/gatewayapi/send-sms`. Needed only for direct GatewayAPI calls (Basic Auth, token as username). |
| `GATEWAYAPI_BASE_URL` | `https://gatewayapi.com/rest` | **Reserved.** Same as above. |
| `DEFAULT_BRAND_SLUG` | `acme-plumbing` | Fallback `brand_slug` in every normalize Code node and every `POST /api/v1/events` body when the inbound payload omits it. |
| `DEFAULT_TIMEZONE` | `America/New_York` | Fallback timezone for human-readable appointment times (03 booking SMS/email, 04 reminder SMS). |
| `INTERNAL_ALERT_WEBHOOK_URL` | Slack/Teams incoming-webhook URL | Team notifications: 02 (new quote), 05 (review request failed), 07 (missed-lead escalation), 08 (🚨 emergency on-call alert). Payload shape: `{"text": "..."}`. |
| `REVIEW_REQUEST_DELAY_MINUTES` | `120` | 05 — Wait node delay between the job-completed webhook and calling `POST /api/v1/reviews/request`. Set to `1` while testing. |
| `REMINDER_LEAD_HOURS` | `24` | 04 — reminder fires at `scheduled_for − REMINDER_LEAD_HOURS` (floored to one minute from now if that moment already passed). |

Notes:

- Numeric variables arrive as strings; the workflows coerce with
  `Number($env.X) || <default>`, so an unset variable falls back safely
  (`REVIEW_REQUEST_DELAY_MINUTES` → 120, `REMINDER_LEAD_HOURS` → 24).
- If `INTERNAL_ALERT_WEBHOOK_URL` is unset, the alert nodes fail softly
  (continue-on-error) — flows still complete, you just get no team pings.
- Rotating `INTERNAL_API_TOKEN` requires updating it in both the backend
  environment and here at the same time.
