# SECTION 10 — Brevo Integration Contract

Extends `docs/BREVO_SETUP.md` (lists 1–4, 7 segments, 10 attributes, folder structure, and the
4 Brevo-native workflows are defined there — that doc is canonical for account setup). This
section adds the sync contract the backend/n8n must obey.

## Roles

Brevo = **marketing mirror + sequence executor**. Postgres owns the data; Brevo receives
projections of it. Brevo never writes back except engagement webhooks (opens/clicks/unsubs).

## Contact identity & create-vs-update

- Identity key in Brevo: **email** when present, else SMS (phone). Postgres identity is phone
  (`customers.phone UNIQUE`) — so **always send both** when available; email-less leads are
  still reachable for SMS-consent purposes and get merged when email arrives later.
- Always call `POST /v3/contacts` with `updateEnabled: true` (upsert) — never branch
  create-vs-update client-side; the shipped `services/brevo.py` already does this.
- On upsert success, store the returned id in `leads.brevo_contact_id` (shipped). Customers
  keep the same Brevo contact — conversion is an attribute/list change, not a new contact.

## Sync rules (when Postgres pushes)

| Postgres change | Brevo action |
|---|---|
| lead created (`/leads`, `/quotes`) | upsert → `list_leads` (id 2) + attributes ✅ shipped |
| lead → customer conversion (first job completed) | upsert → add `list_customers` (3), remove `list_leads` (2); set `LIFETIME_VALUE`, `LAST_JOB_AT` |
| job completed (repeat) | update `LIFETIME_VALUE`, `LAST_JOB_AT` |
| tag applied in Postgres | attribute update (tags project into attributes; see below) |
| lapsed scan (WF-3) | add to `list_reactivation` (4) |
| consent_email=false (webhook or manual) | Brevo blocklist status — do NOT delete the contact |
| privacy erasure | `DELETE /v3/contacts/{id}` then wipe Postgres PII |

Update strategy: **full projection, not diffs** — every sync sends the complete attribute set
for that contact. Idempotent, self-healing, no drift bookkeeping.

## Tagging convention

Postgres kebab-case tags project into Brevo as attribute values, not Brevo "tags":
`WATER_SOURCE=well` ← `well-water` tag; `STATUS=quoted` ← `quote-pending`;
boolean-ish attributes for flow gates (`EMERGENCY=true`). Segments (`seg_*`) key off these
attributes — see BREVO_SETUP's segment table. Rationale: attributes are filterable in segment
rules and visible per-contact; Brevo's tag feature is weaker than its attribute engine.

## Sample requests

Create/update a lead contact (what `services/brevo.py` sends today, plus the postal/consent
fields to add):

```json
POST https://api.brevo.com/v3/contacts
api-key: $BREVO_API_KEY

{
  "email": "maria@example.com",
  "sms": "+15615550142",
  "updateEnabled": true,
  "listIds": [2],
  "attributes": {
    "SERVICE_TYPE": "water_softener",
    "URGENCY": "standard",
    "SOURCE": "website",
    "WATER_SOURCE": "well",
    "CITY": "Loxahatchee",
    "POSTAL_CODE": "33470",
    "STATUS": "new",
    "CONSENT_SMS": true
  }
}
```

Conversion to customer:

```json
{
  "email": "maria@example.com",
  "sms": "+15615550142",
  "updateEnabled": true,
  "listIds": [3],
  "unlinkListIds": [2],
  "attributes": {
    "STATUS": "won",
    "LIFETIME_VALUE": 4850.00,
    "LAST_JOB_AT": "2026-07-15",
    "WATER_SOURCE": "well",
    "CITY": "Loxahatchee",
    "CONSENT_SMS": true
  }
}
```

Attribute definitions (one-time setup, `POST /v3/contacts/attributes/normal/{name}`):
`SERVICE_TYPE,URGENCY,SOURCE,WATER_SOURCE,CITY,POSTAL_CODE,STATUS` → `text`;
`LIFETIME_VALUE` → `float`; `LAST_JOB_AT` → `date`; `CONSENT_SMS` → `boolean`.

## Sync pseudo-code (target shape for `services/brevo.py` evolution)

```
def sync_contact(entity):                      # entity = lead or customer projection
    attrs = project_attributes(entity)          # full set, UPPER_SNAKE
    lists = [3] if entity.is_customer else [2]
    unlink = [2] if entity.is_customer else []
    resp = POST /v3/contacts {email, sms, updateEnabled: true,
                              listIds: lists, unlinkListIds: unlink, attributes: attrs}
    if resp in (200, 201, 204): store brevo_contact_id; return ok
    if resp == 400 and "duplicate_parameter" in body:
        # email and sms belong to two different Brevo contacts → conflict
        existing = GET /v3/contacts/{email}
        PUT /v3/contacts/{existing.id} {attributes, listIds}   # keep email-keyed contact,
        log_conflict(entity, existing)                          # flag the orphan for manual merge
        return ok
    if resp == 429: retry with backoff (n8n leg) or drop (in-request leg — mirror is
                    self-healing on next sync)
    log error; return failed                    # NEVER block the business flow on Brevo
```

## Error & conflict handling rules

1. Brevo failures are **non-fatal everywhere** — the mirror heals on the next sync. Shipped
   client already never raises.
2. `duplicate_parameter` (email vs sms pointing at different contacts) is the one real
   conflict: prefer the **email-keyed** contact, update it, log the orphan. Don't auto-delete.
3. 429 rate limits: in-request syncs drop (logged); n8n syncs retry ×3 with 30s backoff.
4. Weekly reconciliation (optional, post-launch): count Brevo list members vs Postgres
   projections; alert on >2% drift.
