# Acme Plumbing — n8n Workflows

Eight importable workflows orchestrating the Acme Plumbing marketing backend
(`acme-plumbing-backend` FastAPI app). n8n is the orchestration layer; **FastAPI is
the system of record** — every workflow talks to the backend over HTTP Request
nodes (no direct Postgres access, no direct Brevo/GatewayAPI calls: one auth,
logging, and consent path lives in the backend).

## Workflows

| File | Webhook path | What it does |
|---|---|---|
| `01_new_website_lead.json` | `POST /webhook/new-website-lead` | Normalize + validate lead → create in FastAPI (idempotency key derived) → Brevo sync → confirmation SMS if phone → event → respond |
| `02_quote_request.json` | `POST /webhook/quote-request` | Same intake with `lead_type=quote_request` → confirmation email (SMS fallback) → internal team alert → event → respond |
| `03_booking_confirmation.json` | `POST /webhook/booking-confirmation` | Create booking → confirmation SMS (email fallback) with human-formatted local time → `booking_confirmed` event → **schedule a review request** (`scheduled_for + REVIEW_AFTER_APPOINTMENT_HOURS`, dispatched later by 05) → respond |
| `04_appointment_reminder.json` | **Schedule (every 15 min)** | Poll `GET /automations/appointment-reminders/due` → expand → reminder SMS per booking → `appointment_reminder_sent` event (clears it from the next poll) |
| `05_review_request.json` | **Schedule (every 15 min)** | Poll `GET /automations/review-requests/due` → expand → SMS or email per `channel` → `mark-sent` on success / `mark-failed` on error |
| `06_lead_reactivation.json` | `POST /webhook/lead-reactivation` | Accept a batch of stale contacts → filter eligible (inactive ≥ `min_days_inactive`, reachable, SMS consent) → SMS or Brevo per contact → per-contact events → batch summary response |
| `07_missed_lead_recovery.json` | `POST /webhook/missed-lead-recovery` | Internal escalation to team webhook → "we're on it" SMS to customer if phone → event → action summary |
| `08_emergency_plumbing_fast_response.json` | `POST /webhook/emergency-plumbing-fast-response` | Create lead immediately → branch on urgency: emergency gets ack SMS + 🚨 on-call alert + high-priority event + 5-minute-callback response; standard falls through to normal intake |

## Design decisions worth knowing

- **04 and 05 are Schedule-Trigger pollers over the backend's `/automations/*/due`
  queues.** Each fires on an interval, pulls whatever is due, expands the JSON
  array into one item per record, dispatches, then reports the outcome back to
  the backend. The backend owns *when* something is due; n8n owns *sending it*.
- **04 clears its own work via an event.** The due query excludes any booking
  that already has an `appointment_reminder_sent` event, so the workflow only
  logs that event **after** the SMS reports `sent: true`. A send failure leaves
  the booking due and it retries on the next tick (at-least-once). Reminders
  surface once their `scheduled_for` enters the `APPOINTMENT_REMINDER_LEAD_HOURS`
  window (backend-side).
- **05 marks each request terminally.** After sending it calls
  `POST /automations/review-requests/{id}/mark-sent` (success) or `…/mark-failed`
  (failure). `completed`/`canceled` are terminal server-side, so a duplicate
  mark is a safe no-op. **Scheduling** a review request (creating the row) is a
  separate concern handled by **03**, which calls
  `POST /api/v1/automations/review-requests` after a booking is confirmed,
  scheduled for `booking.scheduled_for + REVIEW_AFTER_APPOINTMENT_HOURS`; this
  workflow only dispatches the queue. The `delivery-update` endpoint is for
  relaying provider delivery outcomes and is exercised by the inbound-webhook
  path, not this poller.
- **03 schedules the review at booking time**, assuming the job runs at its
  appointment (there is no job-completion signal in this system yet). If a
  booking is later cancelled or no-shows, the backend's due query already skips
  its review request (`fetch_due` excludes requests whose linked booking is
  `cancelled`/`no_show`), so 05 never dispatches it. The request row stays
  `pending` rather than being explicitly `canceled`; add a cancellation hook
  that flips it if you want that reflected in its status.
- **Idempotency:** lead-creating workflows (01, 02, 08) derive a stable
  `idempotency_key` (djb2 hash of phone/email/message/page_url, or the caller's
  `submission_id`) and send it both in the body and as an `Idempotency-Key`
  header — retries and double-submits return the original lead. 06 relies on
  the eligibility filter + backend contact upsert; 07 expects the caller (the
  cron/query that detects missed leads) not to re-post the same lead.
- **Failure paths:** backend-call nodes use *continue on error* → an IF on the
  response separates success from failure; callers get 422 (validation),
  502 (backend down), or 404 (booking missing) with a JSON error body. SMS,
  Brevo, event-log, and alert calls are non-fatal by design (logged, flow
  continues) — losing a courtesy SMS should never fail the intake.

## Environment variables

Set these on the n8n instance (Settings → Variables, or process env — they are
read via `$env.*`). Full reference: [`env/workflow-variables.md`](env/workflow-variables.md).

`API_BASE_URL`, `INTERNAL_API_TOKEN`, `DEFAULT_BRAND_SLUG`, `DEFAULT_TIMEZONE`,
`INTERNAL_ALERT_WEBHOOK_URL` (+ `BREVO_*` / `GATEWAYAPI_*` reserved for
direct-call variants). The review/reminder timing knobs now live on the backend
(`REVIEW_REQUEST_DEFAULT_DELAY_MINUTES`, `APPOINTMENT_REMINDER_LEAD_HOURS`), since
04/05 poll the backend's due queues rather than waiting in n8n.

## Expected FastAPI endpoints

| Endpoint | Used by |
|---|---|
| `POST /api/v1/leads` | 01, 02, 08 |
| `POST /api/v1/bookings`, `GET /api/v1/bookings/{id}` | 03 |
| `POST /api/v1/events` | 01–04, 06–08 |
| `POST /api/v1/automations/review-requests` (schedule) | 03 |
| `GET /api/v1/automations/appointment-reminders/due` | 04 |
| `GET /api/v1/automations/review-requests/due`, `POST …/{id}/mark-sent`, `POST …/{id}/mark-failed` | 05 |
| `POST /api/v1/reviews/request` | (legacy immediate send; superseded by the 05 poller) |
| `POST /api/v1/integrations/brevo/sync-contact` | 01, 02, 06 |
| `POST /api/v1/integrations/gatewayapi/send-sms` | 01, 03, 04, 05, 06, 07, 08 |
| `POST /api/v1/integrations/resend/send-email` | 02, 03, 05 |

> All endpoints above exist in `acme-plumbing-backend`. The `/automations/*`
> routes require `INTERNAL_API_TOKEN` and honor `ENABLE_AUTOMATION_ENDPOINTS`.

## Import instructions

1. n8n → **Workflows → Import from File** → pick each JSON in `workflows/`
   (or paste the JSON into a new workflow canvas).
2. Set the environment variables above, then restart n8n if you added them
   as process env vars.
3. All workflows import **inactive**. Activate one at a time after testing.
4. Webhook URLs follow n8n's pattern: `https://<n8n-host>/webhook/<path>`
   (test URL: `/webhook-test/<path>` while the editor is open).

## Credentials

**None required by default.** Every external call goes through the FastAPI
backend using the `Authorization: Bearer {{ $env.INTERNAL_API_TOKEN }}` header
set inline on each HTTP Request node — there are no n8n credential objects to
relink. If you later switch any HTTP Request node to call Brevo or GatewayAPI
directly, create Header Auth (Brevo `api-key`) / Basic Auth (GatewayAPI token
as username) credentials and relink those specific nodes; that is the only
manual relinking scenario.

## Known assumptions

- Single brand (`acme-plumbing`) — payloads may override `brand_slug`.
- Phone numbers arrive E.164; validation rejects otherwise (422).
- `INTERNAL_ALERT_WEBHOOK_URL` accepts `{"text": "..."}` (Slack-compatible).
- Workflow 06 receives its batch via webhook from a scheduler/cron you own;
  n8n does not query the database for stale contacts itself.
- Event names posted by n8n (`lead_intake_completed`, `booking_confirmed`,
  `appointment_reminder_sent`, …) are free-form in the starter's `event_log`.
- n8n ≥ 1.20 (Webhook v2, Schedule Trigger v1.2, IF v2.2, HTTP Request v4.2, Code v2, Merge v3).

## Recommended testing order

1. **01 New Website Lead** — has pinned sample data on the webhook node; run in
   the editor first, then `curl` the test URL. Verify lead + event rows.
2. **08 Emergency** — same payload with `"urgency": "emergency"`; check both
   branches (emergency + standard).
3. **02 Quote Request** — email path and SMS-fallback path.
4. **03 Booking Confirmation** — creates the booking you need for…
5. **04 Appointment Reminder** — create a booking within the backend's
   `APPOINTMENT_REMINDER_LEAD_HOURS` window, then **Execute Workflow** on the
   Schedule Trigger; confirm the SMS fires once and a repeat run finds nothing
   due (the `appointment_reminder_sent` event cleared it).
6. **05 Review Request** — schedule one via
   `POST /api/v1/automations/review-requests` with `delay_minutes=0`, then
   **Execute Workflow**; confirm SMS/email dispatch and that the request flips
   to `sent`. A second run finds it no longer due.
7. **07 Missed Lead Recovery**, then **06 Lead Reactivation** (batch of 2–3
   contacts incl. one ineligible, one email-only).
