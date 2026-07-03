# SECTION 13 — n8n Node-by-Node Outlines

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
