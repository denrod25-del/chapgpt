# SECTION 12 — n8n Workflow Specs

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
