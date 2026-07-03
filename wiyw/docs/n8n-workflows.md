# n8n Workflows

*(Mirrors blueprint sections 12–13. The importable JSONs in `n8n/` are canonical for WF-4..7.)*

## Part 1 — Workflow specs

Eight workflows. **Placement rule (from n8n/WORKFLOWS.md, canonical):** instant-response flows
(1, 2, 3, 8) run **synchronously inside FastAPI** today — they must fire in the request path.
Their n8n specs below are the *async migration target*: build one only when moving that flow
out of the API, and **disable the in-API sends the same deploy** (double-send hazard).
Scheduled/delayed flows (4, 5, 6, 7) live in n8n now — JSONs shipped in `n8n/`.

Common conventions for every workflow:
- **Credentials:** Postgres (VPS DB), GatewayAPI (HTTP Basic, token as user), Resend (Bearer),
  Brevo (`api-key` header) — reuse the 4 shared credentials, remap `REPLACE_*` on import.
- **Run accounting:** first node after trigger inserts an `automation_runs` row
  (`status=running`, `workflow_key`, `trigger_type`); last node closes it
  (`status=success|partial|failed`, `items_*` counters). Failure path = n8n Error Trigger
  workflow updates the run row + SMS to `OWNER_ALERT_PHONE` (one shared error workflow for all).
- **Retries:** HTTP Request nodes: retry ×3, 30s backoff, `continueOnFail: true` then an IF on
  `statusCode` for the fallback branch. Postgres nodes: no auto-retry (transactional; the next
  cron tick is the retry).
- **Idempotency:** every workflow keys off a DB flag/tag/comm-log guard so a re-run never
  double-sends (specific guard listed per workflow).
- **Metrics:** every send emits a taxonomy event; every run closes `automation_runs` — the
  dashboard reads those two tables, workflows emit nothing else.

---

## WF-1 `wf1_new_website_lead` — status: **in FastAPI (`POST /leads`)** ✅

- **Goal:** every lead gets confirmation (email+SMS) within seconds; owner alerted; Brevo mirrored.
- **n8n variant (migration target):** Webhook trigger `POST /wh/new-lead` receiving
  `{lead_id, full_name, phone, email, service_type, urgency, water_source, source}` from the
  backend (via `webhook_deliveries`), then: fetch lead (Postgres) → parallel legs: Resend
  confirmation email / GatewayAPI confirmation SMS / GatewayAPI owner alert / Brevo upsert →
  comm-log + `lead_created` event writes → respond 200.
- **Branching:** `email` empty → skip email leg. `urgency=emergency` → hand off to WF-8 (do not
  duplicate its sends).
- **Idempotency guard:** comm log `template='sms_lead_confirm'` for this lead_id.
- **Tags:** `lead-new` (+ `well-water`/`city-water` auto-tag by `water_source`).

## WF-2 `wf2_quote_request` — status: **in FastAPI (`POST /quotes`)** ✅

- **Goal:** high-intent quote lead acknowledged instantly, owner alerted, quote follow-up
  sequence entered.
- **Flow (as shipped, for reference):** insert lead `status=quoted` → `quote_requested` event →
  tag `quote-pending` → SMS ack → owner SMS → Brevo upsert (`STATUS=quoted` attribute puts the
  contact into Brevo's `wf_quote_followup` Day 0/2/5 sequence — the nurture itself is
  Brevo-native, not n8n).
- **n8n variant:** same shape as WF-1 with the `quote-pending` tag and Brevo attribute set.
- **Idempotency guard:** tag `quote-pending` presence per lead.

## WF-3 `wf3_booking_confirmation` — status: **in FastAPI (`POST /bookings`)** ✅

- **Goal:** booking creates instant SMS ("Reply C to confirm") + email confirmation.
- **Flow (shipped):** insert booking → `appointment_booked` event → tag `booked` → GatewayAPI
  SMS + Resend email.
- **n8n additions worth building even while sends stay in FastAPI:** inbound "C" reply handler —
  GatewayAPI inbound webhook (via backend inbox) matches phone → most recent
  `status='scheduled'` booking → `UPDATE bookings SET status='confirmed'` + `booking_confirmed`
  event.
- **Idempotency guard:** booking insert is the trigger; confirmation handler is idempotent
  (`status='confirmed'` re-set is a no-op).

## WF-4 `wf1_appointment_reminders` — status: **built** (`n8n/wf1_appointment_reminders.json`)

- **Goal:** cut no-shows with 24h and 2h SMS reminders.
- **Trigger:** Schedule `*/15 * * * *`.
- **Input:** Postgres scan — bookings `status IN (scheduled,confirmed)`, consent_sms, window
  `[now+23h, now+24h]` (and a second branch `[now+105min, now+120min]`).
- **Flow:** scan → split → GatewayAPI SMS → IF status≥300 → Resend email fallback
  (`failed_sms_fell_back_email` comm log) → set `reminder_24h_sent`/`reminder_2h_sent` → comm
  log → `appointment_reminder_sent` event.
- **Idempotency guard:** the `reminder_*_sent` booleans — set even on fallback so no loop.
- **Metrics:** no-show rate with vs without reminder; SMS delivery rate.

## WF-5 `wf2_review_request` — status: **built** (`n8n/wf2_review_request.json`)

- **Goal:** review request 2h after job completion; SMS leg primary, Brevo email leg for
  no-SMS-consent; one nudge after 3 days if no review.
- **Trigger:** Schedule `*/30 * * * *`.
- **Flow:** scan jobs (`completed_at < now()-2h`, `review_requested=false`) → split → IF
  consent_sms → GatewayAPI `sms_review` with `{REVIEW_SHORTLINK_BASE}/{job_id}` / ELSE Brevo
  review email template → `UPDATE jobs SET review_requested=true` → tag `review-requested` →
  `review_request_sent` event. Companion WF-5b (daily): requested >3d ago, no `review_received`
  event, no prior nudge in comm logs → one Brevo nudge, bounded.
- **Idempotency guards:** `jobs.review_requested` flag; nudge guard via comm-log lookup.
- **Metrics:** request→received conversion; time-to-review.

## WF-6 `wf3_reactivation` — status: **built** (`n8n/wf3_reactivation.json`)

- **Goal:** win back customers idle >9 months ("annual water-quality check" angle).
- **Trigger:** Schedule Mon 09:00 (`0 9 * * 1`).
- **Flow:** scan lapsed customers excluding anyone `reactivation`-tagged in the last 90 days →
  split → tag `reactivation` → Brevo reactivation email → **Wait 7 days** → check
  `email_opened`/`email_clicked` events since send → IF engaged → tag `reactivation-warm`;
  ELSE IF consent_sms → GatewayAPI nudge SMS.
- **Idempotency guard:** 90-day tag-recency exclusion in the scan SQL.
- **Metrics:** reactivation→booking rate; warm-tag count.

## WF-7 `wf4_missed_lead_recovery` — status: **built** (`n8n/wf4_missed_lead_recovery.json`)

- **Goal:** no lead waits >15 min uncontacted.
- **Trigger:** Schedule `*/5 * * * *`.
- **Flow:** scan leads `status='new' AND contacted_at IS NULL AND created_at ∈ [now-2h, now-15m]`
  → exclude leads with a `sms_missed_recovery` comm log → split → owner escalation SMS →
  reassurance SMS to lead → comm log `template='sms_missed_recovery'`.
- **Fallback:** GatewayAPI down → owner email via Resend.
- **Idempotency guard:** the comm-log template exclusion; 2h upper bound stops ancient re-alerts.
- **Metrics:** recovery→contacted rate; median time-to-contact.

## WF-8 `wf8_emergency_fast_response` — status: **in FastAPI (`POST /leads`)** ✅

- **Goal:** emergency leads get a "we'll call in 5 minutes" promise SMS + escalated owner alert
  (🚨 prefix) instantly.
- **Flow (shipped):** `urgency=emergency OR service_type=emergency` inside `POST /leads` →
  `emergency` tag → promise SMS + escalated owner SMS.
- **n8n escalation ladder (build post-launch, this part is genuinely n8n-shaped):** Webhook from
  backend on emergency lead → **Wait 5 min** → check `contacted_at` still NULL → second owner
  SMS + call-forward attempt → **Wait 10 min** → still NULL → SMS to backup tech phone +
  `automation_runs` partial flag. Guard: skip all escalation once `contacted_at` set.
- **Idempotency guard:** `emergency` tag + comm-log check per escalation step.
- **Metrics:** emergency time-to-contact p50/p95 (from `created_at` → `contacted_at`).

---

Also shipped as spec: **WF-9 review monitoring** (`n8n/WF5_review_monitoring.md`) — Semrush →
Postgres `reviews` upsert with the migration-004 dedupe hash. Not in the prompt's eight; listed
so nobody rebuilds it accidentally.

---

## Part 2 — Node-by-node outlines

Node types used: Webhook, Respond to Webhook, Schedule Trigger, Postgres, HTTP Request, IF,
Switch, Split Out, Merge, Wait, Set, Code. Every Postgres node: parameterized queries only.
Every workflow: prepend a Postgres node opening an `automation_runs` row and append one closing
it (omitted below for brevity — same two nodes everywhere, `workflow_key` differs).

For WF-4/5/6/7 the shipped JSONs in `n8n/` are the source of truth; outlines here match them.

## WF-1 · New Website Lead (n8n variant — only when leaving FastAPI)

| # | Node | Purpose / key config |
|---|------|---------------------|
| 1 | **Webhook** `wh_new_lead` | `POST /wh/new-lead`, auth: header token = `INTERNAL_API_TOKEN`. Input: `{lead_id}` |
| 2 | **Respond to Webhook** | immediate `{"ok":true}` — never make the backend wait |
| 3 | **Postgres** `fetch_lead` | `SELECT full_name, phone, email, service_type, urgency, water_source, source FROM leads WHERE id=$1` |
| 4 | **IF** `is_emergency` | `urgency='emergency' OR service_type='emergency'` → true branch also fires WF-8 webhook |
| 5 | **HTTP** `send_confirm_sms` | GatewayAPI mtsms; message = `sms_lead_confirm` copy; retry ×3/30s |
| 6 | **IF** `has_email` | email non-empty |
| 7 | **HTTP** `send_confirm_email` | Resend `/emails`, `txn_lead_confirmation` HTML |
| 8 | **HTTP** `owner_alert_sms` | GatewayAPI → `OWNER_ALERT_PHONE` |
| 9 | **HTTP** `brevo_upsert` | `POST /v3/contacts` upsert, list 2, attributes projection |
| 10 | **Postgres** `log_comms` | INSERT communication_logs rows (from items merged off 5/7) |
| 11 | **Postgres** `emit_event` | INSERT events `lead_created` |

## WF-2 · Quote Request (n8n variant)

| # | Node | Purpose / key config |
|---|------|---------------------|
| 1 | **Webhook** `wh_quote_request` | input `{lead_id}` |
| 2 | **Respond to Webhook** | fast ack |
| 3 | **Postgres** `fetch_lead` | lead by id |
| 4 | **HTTP** `ack_sms` | GatewayAPI "we're preparing your quote" |
| 5 | **HTTP** `owner_sms` | GatewayAPI quote alert |
| 6 | **HTTP** `brevo_upsert` | attributes `STATUS=quoted` → enters Brevo `wf_quote_followup` |
| 7 | **Postgres** `tag_and_log` | tag `quote-pending` (idempotency guard: `ON CONFLICT DO NOTHING` on the partial unique index), comm logs, `quote_requested` event |

## WF-3 · Booking Confirmation (n8n variant + inbound-C handler)

Outbound variant = WF-1 shape with booking fetch and `sms_booking_confirm`/`txn_booking_confirmation`
templates. The genuinely new piece is the inbound confirm handler:

| # | Node | Purpose / key config |
|---|------|---------------------|
| 1 | **Webhook** `wh_sms_inbound` | fed by backend inbox processor on GatewayAPI MO messages |
| 2 | **IF** `is_confirm` | `message.trim().upper() IN ('C','CONFIRM','YES')` |
| 3 | **Postgres** `find_booking` | `SELECT b.id FROM bookings b JOIN customers c ON c.id=b.customer_id WHERE c.phone=$1 AND b.status='scheduled' AND b.scheduled_for > now() ORDER BY b.scheduled_for LIMIT 1` |
| 4 | **IF** `found` | empty result → end (log only) |
| 5 | **Postgres** `confirm` | `UPDATE bookings SET status='confirmed' WHERE id=$1` |
| 6 | **Postgres** `emit_event` | `booking_confirmed` |
| 7 | **HTTP** `thanks_sms` | GatewayAPI "You're confirmed — see you then!" |

## WF-4 · Appointment Reminder (built — `wf1_appointment_reminders.json`)

| # | Node | Purpose / key config |
|---|------|---------------------|
| 1 | **Schedule Trigger** `every_15min` | cron `*/15 * * * *` |
| 2 | **Postgres** `fetch_due_24h` | window `[now+23h, now+24h]`, `reminder_24h_sent=false`, `consent_sms=true`, join customers |
| 3 | **Split Out** | one item per booking |
| 4 | **Set** `build_message` | format `scheduled_for` in brand TZ; compose `sms_reminder_24h` copy |
| 5 | **HTTP** `send_sms` | GatewayAPI; `continueOnFail: true` |
| 6 | **IF** `sms_failed` | `statusCode >= 300` |
| 6a | **HTTP** `email_fallback` | Resend reminder email; comm-log status `failed_sms_fell_back_email` |
| 7 | **Postgres** `mark_sent` | `UPDATE bookings SET reminder_24h_sent=true WHERE id=$1` — set on both branches (loop guard) |
| 8 | **Postgres** `log_comm` | INSERT communication_logs `sms_reminder_24h` |
| 9 | **Postgres** `emit_event` | `appointment_reminder_sent` payload `{window:'24h', channel}` |
| 10–17 | duplicate of 2–9 | 2h branch: window `[now+105m, now+120m]`, `reminder_2h_sent` |

## WF-5 · Review Request (built — `wf2_review_request.json`)

| # | Node | Purpose / key config |
|---|------|---------------------|
| 1 | **Schedule Trigger** `every_30min` | cron `*/30 * * * *` |
| 2 | **Postgres** `fetch_completed` | jobs `completed_at < now()-'2h'`, `review_requested=false`, join customers |
| 3 | **Split Out** | per job |
| 4 | **IF** `consent_sms` | true → SMS leg, false → email leg |
| 5a | **HTTP** `review_sms` | GatewayAPI `sms_review`; link `{REVIEW_SHORTLINK_BASE}/{job_id}` |
| 5b | **HTTP** `review_email` | Brevo transactional-template send (email leg of the split flow) |
| 6 | **Merge** | rejoin branches |
| 7 | **Postgres** `mark_requested` | `UPDATE jobs SET review_requested=true` (idempotency flag) |
| 8 | **Postgres** `tag_customer` | tag `review-requested` |
| 9 | **Postgres** `emit_event` | `review_request_sent` payload `{job_id, channel}` |

WF-5b nudge (daily 10:00): Schedule → Postgres scan (`review_requested=true`, >3d, no
`review_received` event, no `mkt_review_nudge` comm log) → Split → Brevo nudge → comm log.

## WF-6 · Lead Reactivation (built — `wf3_reactivation.json`)

| # | Node | Purpose / key config |
|---|------|---------------------|
| 1 | **Schedule Trigger** `mon_9am` | cron `0 9 * * 1` |
| 2 | **Postgres** `fetch_lapsed` | `last_job_at < now()-'9 months'`, NOT tagged `reactivation` in 90d |
| 3 | **Split Out** | per customer |
| 4 | **Postgres** `tag_reactivation` | INSERT entity_tags (guard for next scan) |
| 5 | **HTTP** `brevo_reactivation` | reactivation template; "annual water-quality check" angle |
| 6 | **Wait** `7_days` | resume same item |
| 7 | **Postgres** `check_engagement` | any `email_opened`/`email_clicked` for customer since node 5 |
| 8 | **IF** `engaged` | true → node 9, false → node 10 |
| 9 | **Postgres** `tag_warm` | tag `reactivation-warm` |
| 10 | **IF** `consent_sms` | true → **HTTP** GatewayAPI nudge SMS + comm log |

## WF-7 · Missed Lead Recovery (built — `wf4_missed_lead_recovery.json`)

| # | Node | Purpose / key config |
|---|------|---------------------|
| 1 | **Schedule Trigger** `every_5min` | cron `*/5 * * * *` |
| 2 | **Postgres** `fetch_stale` | `status='new' AND contacted_at IS NULL AND created_at BETWEEN now()-'2h' AND now()-'15m'` |
| 3 | **Postgres** `guard_not_recovered` | exclude leads having comm log `template='sms_missed_recovery'` |
| 4 | **Split Out** | per lead |
| 5 | **HTTP** `owner_escalation` | GatewayAPI → `OWNER_ALERT_PHONE` "uncontacted 15+ min"; on fail → **HTTP** Resend owner email |
| 6 | **HTTP** `lead_reassurance` | GatewayAPI "we'll call you shortly" |
| 7 | **Postgres** `log_comm` | `template='sms_missed_recovery'` (the guard for node 3) |

## WF-8 · Emergency Fast-Response Escalation (build post-launch; sends live in FastAPI)

| # | Node | Purpose / key config |
|---|------|---------------------|
| 1 | **Webhook** `wh_emergency_lead` | from backend on emergency lead; input `{lead_id}` |
| 2 | **Respond to Webhook** | fast ack |
| 3 | **Wait** `5_min` | escalation window 1 |
| 4 | **Postgres** `check_contacted` | `SELECT contacted_at FROM leads WHERE id=$1` |
| 5 | **IF** `still_uncontacted` | `contacted_at IS NULL` — false → end (success) |
| 6 | **HTTP** `owner_sms_2` | GatewayAPI "🚨 STILL UNCONTACTED: {name} {phone}" |
| 7 | **Wait** `10_min` | escalation window 2 |
| 8 | **Postgres** `check_contacted_2` | re-check |
| 9 | **IF** `still_uncontacted_2` | false → end |
| 10 | **HTTP** `backup_tech_sms` | GatewayAPI → `BACKUP_TECH_PHONE` ⟨add env var⟩ |
| 11 | **Postgres** `close_run_partial` | `automation_runs` status=`partial`, details `{escalated: 2}` |
