# WiYW — n8n Workflows (Section 6, node-by-node)

Division of responsibility: **synchronous, instant-response** automations (New Lead #1, Emergency #8)
live in the FastAPI `/leads` route — they must fire in the request path with no polling delay.
The **scheduled / delayed** automations below live in n8n. Each references the Postgres source of
truth and the same providers (Resend, GatewayAPI, Brevo).

Connection reused across workflows:
- **Postgres** credential → your VPS DB
- **GatewayAPI** → HTTP Request node, Basic Auth (token as username, blank password)
- **Resend** → HTTP Request node, Bearer token
- **Brevo** → HTTP Request node, `api-key` header

---

## WF-1 · Appointment Reminder (Automation #4)

**Trigger:** Schedule node — every 15 min.

| # | Node | Type | Logic |
|---|------|------|-------|
| 1 | Every 15 min | Schedule Trigger | cron `*/15 * * * *` |
| 2 | Fetch due 24h | Postgres | `SELECT b.id, c.full_name, c.phone, b.scheduled_for FROM bookings b JOIN customers c ON c.id=b.customer_id WHERE b.status IN ('scheduled','confirmed') AND b.reminder_24h_sent=false AND b.scheduled_for BETWEEN now()+interval '23 hours' AND now()+interval '24 hours' AND c.consent_sms=true` |
| 3 | Split | Split Out | one item per booking |
| 4 | Send 24h SMS | HTTP → GatewayAPI | body: sender=WiYW, message=`sms_reminder`, recipients=[{msisdn}] |
| 5 | Mark sent | Postgres | `UPDATE bookings SET reminder_24h_sent=true WHERE id=$1` |
| 6 | Log comm | Postgres | INSERT communication_logs (channel=sms, template=sms_reminder_24h, status=sent) |
| 7 | Emit event | Postgres | INSERT events (event_name='appointment_reminder_sent', payload={channel:'sms',window:'24h'}) |

**Second branch (2h window):** duplicate nodes 2–7 with `reminder_2h_sent` and `BETWEEN now()+interval '105 minutes' AND now()+interval '120 minutes'`.

**Fallback:** IF node after node 4 — if GatewayAPI status ≥ 300 → Resend email branch → still mark sent to avoid loop, but log status=`failed_sms_fell_back_email`.

**Metrics to monitor:** no-show rate on bookings with vs without reminder_sent; SMS delivery rate.

---

## WF-2 · Post-Job Review Request (Automation #5)

**Trigger:** Schedule node — every 30 min.

| # | Node | Type | Logic |
|---|------|------|-------|
| 1 | Every 30 min | Schedule Trigger | cron `*/30 * * * *` |
| 2 | Fetch completed jobs | Postgres | `SELECT j.id, c.full_name, c.phone, c.consent_sms FROM jobs j JOIN customers c ON c.id=j.customer_id WHERE j.completed_at IS NOT NULL AND j.review_requested=false AND j.completed_at < now()-interval '2 hours'` |
| 3 | Split | Split Out | per job |
| 4 | Branch on consent | IF | consent_sms == true |
| 5a| Send review SMS | HTTP → GatewayAPI | `sms_review` with `{REVIEW_SHORTLINK_BASE}/{job_id}` |
| 5b| Send review email | HTTP → Brevo (fallback) | if no SMS consent, trigger Brevo review email template |
| 6 | Mark requested | Postgres | `UPDATE jobs SET review_requested=true WHERE id=$1` |
| 7 | Tag customer | Postgres | INSERT entity_tags → tag `review-requested` |
| 8 | Emit event | Postgres | event_name='review_request_sent' |

**Delayed follow-up:** a separate WF-2b (daily) selects jobs where `review_requested=true`
AND no `review_received` event AND requested > 3 days ago → send Brevo nudge email. Bounded: stop after one nudge (check for existing nudge in communication_logs).

**Metrics:** review_request_sent → review_received conversion; time-to-review.

---

## WF-3 · Re-engagement / Reactivation (Automation #6)

**Trigger:** Schedule — weekly, Mon 09:00 (`0 9 * * 1`).

| # | Node | Type | Logic |
|---|------|------|-------|
| 1 | Weekly Mon 9am | Schedule Trigger | cron `0 9 * * 1` |
| 2 | Fetch lapsed | Postgres | `SELECT id, full_name, email, phone, consent_email, consent_sms FROM customers WHERE last_job_at < now()-interval '9 months' AND id NOT IN (SELECT customer_id FROM entity_tags et JOIN tags t ON t.id=et.tag_id WHERE t.name='reactivation' AND et.applied_at > now()-interval '90 days')` (dedup: don't re-hit within 90 days) |
| 3 | Split | Split Out | per customer |
| 4 | Tag reactivation | Postgres | INSERT entity_tags → `reactivation` |
| 5 | Send email | HTTP → Brevo | reactivation template; WiYW angle: "annual water-quality check / softener service" |
| 6 | Wait 7 days | Wait node | |
| 7 | Check engagement | Postgres | any email_opened/email_clicked event for this customer since step 5? |
| 8 | IF opened+clicked | IF | → tag `reactivation-warm` |
| 9 | ELSE + consent_sms | IF | → GatewayAPI SMS nudge |

**Metrics:** reactivation → booking rate; warm-tag count.

---

## WF-4 · Missed Lead Recovery (Automation #7)

**Trigger:** Schedule — every 5 min.

| # | Node | Type | Logic |
|---|------|------|-------|
| 1 | Every 5 min | Schedule Trigger | cron `*/5 * * * *` |
| 2 | Fetch stale new leads | Postgres | `SELECT id, full_name, phone, service_type FROM leads WHERE status='new' AND contacted_at IS NULL AND created_at < now()-interval '15 minutes' AND created_at > now()-interval '2 hours'` (upper bound prevents re-alerting ancient leads) |
| 3 | Guard: not already recovered | Postgres | exclude leads with a communication_logs row template='sms_missed_recovery' |
| 4 | Split | Split Out | per lead |
| 5 | Owner escalation SMS | HTTP → GatewayAPI | to OWNER_ALERT_PHONE: "Lead {name} uncontacted 15+ min" |
| 6 | Reassurance SMS to lead | HTTP → GatewayAPI | "We got your request and will call you shortly." |
| 7 | Log comm | Postgres | template='sms_missed_recovery' |

**Fallback:** if GatewayAPI down → owner email via Resend.
**Metrics:** recovery → contacted rate; median time-to-contact.

---

## Reference (in FastAPI, NOT n8n)

- **WF New Lead (#1)** and **Emergency (#8)** run synchronously in `POST /leads`. Documented here for completeness; do not duplicate in n8n or you double-send.

## Import notes
- Each workflow ships as a JSON file (`wf1_reminders.json`, etc.) importable via n8n → Import from File.
- The JSON files use placeholder credential IDs; re-map to your credentials on import.
- All Postgres nodes use parameterized queries (`$1`), never string interpolation.
