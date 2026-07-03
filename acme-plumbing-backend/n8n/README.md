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
| `03_booking_confirmation.json` | `POST /webhook/booking-confirmation` | Create booking → confirmation SMS (email fallback) with human-formatted local time → `booking_confirmed` event → respond |
| `04_appointment_reminder.json` | `POST /webhook/appointment-reminder` | Fetch booking → respond "scheduled" → **Wait until** `scheduled_for − REMINDER_LEAD_HOURS` → re-check booking still active → reminder SMS → event |
| `05_review_request.json` | `POST /webhook/review-request` | Validate job payload → respond "scheduled" → **Wait** `REVIEW_REQUEST_DELAY_MINUTES` → `POST /reviews/request` (backend sends the actual message legs) → event or internal alert on failure |
| `06_lead_reactivation.json` | `POST /webhook/lead-reactivation` | Accept a batch of stale contacts → filter eligible (inactive ≥ `min_days_inactive`, reachable, SMS consent) → SMS or Brevo per contact → per-contact events → batch summary response |
| `07_missed_lead_recovery.json` | `POST /webhook/missed-lead-recovery` | Internal escalation to team webhook → "we're on it" SMS to customer if phone → event → action summary |
| `08_emergency_plumbing_fast_response.json` | `POST /webhook/emergency-plumbing-fast-response` | Create lead immediately → branch on urgency: emergency gets ack SMS + 🚨 on-call alert + high-priority event + 5-minute-callback response; standard falls through to normal intake |

## Design decisions worth knowing

- **04 uses Webhook + Wait Until, not a Schedule Trigger.** The backend (or the
  booking workflow) posts each booking here once; the workflow computes
  `scheduled_for − REMINDER_LEAD_HOURS`, responds immediately, sleeps until that
  moment, then **re-fetches the booking** and only sends if status is still
  `pending/scheduled/confirmed`. This avoids a polling loop and needs no
  "list due bookings" endpoint. Swap to a Schedule Trigger + query pattern
  later if you outgrow one-execution-per-booking.
- **05 does not send the review SMS itself.** `POST /api/v1/reviews/request` owns
  the message legs and the `review_requested` claim flag — calling it from n8n
  and also texting from n8n would double-send. The workflow schedules, calls,
  and reports; a 409 (already requested) lands on the failure branch.
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
`INTERNAL_ALERT_WEBHOOK_URL`, `REVIEW_REQUEST_DELAY_MINUTES`, `REMINDER_LEAD_HOURS`
(+ `BREVO_*` / `GATEWAYAPI_*` reserved for direct-call variants).

## Expected FastAPI endpoints

| Endpoint | Used by |
|---|---|
| `POST /api/v1/leads` | 01, 02, 08 |
| `POST /api/v1/bookings`, `GET /api/v1/bookings/{id}` | 03 · 04 |
| `POST /api/v1/events` | all |
| `POST /api/v1/reviews/request` | 05 |
| `POST /api/v1/integrations/brevo/sync-contact` | 01, 02, 06 |
| `POST /api/v1/integrations/gatewayapi/send-sms` | 01, 03, 04, 06, 07, 08 |
| `POST /api/v1/integrations/resend/send-email` | 02, 03 |

> Starter-repo note: `leads`, `bookings`, and `events` exist in
> `acme-plumbing-backend` today. `reviews/request` and the three
> `integrations/*` routes are the next build step (see the backend README);
> until they exist those calls land on each workflow's non-fatal failure path.

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
- n8n ≥ 1.20 (Webhook v2, IF v2.2, HTTP Request v4.2, Code v2, Merge v3).

## Recommended testing order

1. **01 New Website Lead** — has pinned sample data on the webhook node; run in
   the editor first, then `curl` the test URL. Verify lead + event rows.
2. **08 Emergency** — same payload with `"urgency": "emergency"`; check both
   branches (emergency + standard).
3. **02 Quote Request** — email path and SMS-fallback path.
4. **03 Booking Confirmation** — creates the booking you need for…
5. **04 Appointment Reminder** — temporarily set `REMINDER_LEAD_HOURS` high so
   the wait floors to +1 minute; confirm re-check + SMS; cancel a booking to
   test the skip branch.
6. **05 Review Request** — set `REVIEW_REQUEST_DELAY_MINUTES=1`; test the 409
   failure branch by posting the same `job_id` twice.
7. **07 Missed Lead Recovery**, then **06 Lead Reactivation** (batch of 2–3
   contacts incl. one ineligible, one email-only).
