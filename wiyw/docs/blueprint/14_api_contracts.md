# SECTION 14 — API Contracts (concrete examples)

All examples verified against the shipped backend where marked ✅.

## Create lead ✅ (exact request/response reproduced from a live boot this session)

```http
POST /leads            (target: /api/v1/leads)
Content-Type: application/json
Idempotency-Key: 7f3d9c1a-2e4b-4f6a-9c8d-1a2b3c4d5e6f

{
  "full_name": "Maria Gonzalez",
  "phone": "+15615550142",
  "email": "maria@example.com",
  "service_type": "water_softener",
  "urgency": "standard",
  "water_source": "well",
  "message": "Rust stains on fixtures, on a private well in Loxahatchee",
  "source": "website",
  "source_medium": "organic",
  "source_campaign": null,
  "landing_page": "/well-water-treatment",
  "city": "Loxahatchee",
  "postal_code": "33470"
}
```
```json
201 → {"id": "558164f4-35e9-4b02-b421-ce10ffe6cf60", "status": "new"}
422 → {"detail": [{"loc": ["body","phone"], "msg": "Assertion failed, phone must be E.164 (e.g. +15615550123)", "type": "assertion_error"}]}
```
Side effects: lead row (brand_id auto), `form_submitted` event, tags `lead-new`+`well-water`,
confirmation email+SMS, owner SMS, Brevo upsert.

## Create booking ✅

```http
POST /bookings         (internal bearer auth at v1)
{
  "customer_id": "9a2f6c1e-8b3d-4e5f-a1b2-c3d4e5f6a7b8",
  "lead_id": "558164f4-35e9-4b02-b421-ce10ffe6cf60",
  "scheduled_for": "2026-07-10T13:00:00-04:00",
  "service_type": "water_softener"
}
```
```json
201 → {"id": "b7c14d2e-…", "status": "scheduled"}
404 → {"detail": "customer not found"}
422 → scheduled_for in the past
```
Side effects: `appointment_booked` event, `booked` tag, SMS "Reply C to confirm" + email.

## Request review (new route)

```http
POST /api/v1/reviews/request
Authorization: Bearer $INTERNAL_API_TOKEN
Idempotency-Key: 0b9e…

{"job_id": "e4a7…", "delay_hours": 0}
```
```json
200 → {"job_id": "e4a7…", "scheduled": true, "channel": "sms",
       "review_link": "https://whatsinyourwater.com/r/e4a7…"}
409 → {"detail": "review already requested for this job"}
```

## Sync Brevo contact (new route; provider call shape ✅ matches services/brevo.py)

```http
POST /api/v1/integrations/brevo/sync-contact
Authorization: Bearer $INTERNAL_API_TOKEN

{
  "email": "maria@example.com",
  "phone": "+15615550142",
  "list_ids": [2],
  "attributes": {"SERVICE_TYPE": "water_softener", "WATER_SOURCE": "well",
                 "CITY": "Loxahatchee", "STATUS": "new"}
}
```
```json
200 → {"contact_id": "512"}
422 → attribute name not UPPER_SNAKE / phone not E.164
502 → {"detail": "brevo unavailable"}   (n8n retries)
```

## Send SMS (new route; GatewayAPI call shape ✅ matches services/sms.py)

```http
POST /api/v1/integrations/gatewayapi/send-sms
Authorization: Bearer $INTERNAL_API_TOKEN
Idempotency-Key: 51c2…

{
  "to": "+15615550142",
  "message": "What's in Your Water: Reminder — your water softener install is tomorrow at 1:00 PM. Reply C to confirm.",
  "template": "sms_reminder_24h",
  "customer_id": "9a2f6c1e-…"
}
```
```json
200 → {"sent": true, "provider_msg_id": "4890553880"}
200 → {"sent": false, "provider_msg_id": null}     (provider refused; comm log status=failed)
```

Underlying GatewayAPI wire call:
```json
POST https://gatewayapi.com/rest/mtsms   (Basic auth: token as username)
{"sender": "WiYW", "message": "…", "recipients": [{"msisdn": 15615550142}]}
→ {"ids": [4890553880]}
```

## Receive webhook (GatewayAPI DLR example, inbox pattern)

```http
POST /api/v1/webhooks/gatewayapi/$GATEWAYAPI_WEBHOOK_SECRET
Content-Type: application/json

{"id": 4890553880, "msisdn": 15615550142, "time": 1751500000,
 "status": "DELIVERED", "userref": "sms_reminder_24h"}
```
```json
200 → {"ok": true, "inbox_id": "3f6a…"}          (first delivery)
200 → {"ok": true, "duplicate": true}             (provider retry — deduped on {id}:{status})
```
Async side effects: comm log status→`delivered` by `provider_msg_id`, `sms_delivered` event.
Inbound STOP variant: `{"msisdn": 15615550142, "message": "STOP"}` → `consent_sms=false` +
`contact_unsubscribed` event.
