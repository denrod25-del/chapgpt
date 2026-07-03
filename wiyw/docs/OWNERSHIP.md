# OWNERSHIP.md — System Ownership Contract

Canonical division of responsibility for the WiYW marketing stack. Read this before wiring
any new integration. Violating these boundaries causes deliverability damage, data drift, or
double-sends.

## System of record
**Postgres is the source of truth for all contact, lead, customer, booking, job, and review data.**
Every other system is a mirror or a specialized tool. Data flows OUT of Postgres to mirrors;
never treat a mirror as authoritative.

## Ownership table

| Domain | Owner | Must NOT own |
|--------|-------|--------------|
| Marketing email: campaigns, segments, nurture/drip, lists | **Brevo** | transactional receipts, SEO |
| Transactional email: confirmations, system/owner notices, review-request email leg | **Resend** (primary), **Mailgun** (failover + inbound parse) | campaigns, nurture, segments |
| SMS: confirmations, reminders, review-request SMS leg, owner alerts | **GatewayAPI** | marketing blasts without consent |
| Local SEO: listings/citations, map rank, position tracking, review monitoring, on-page recs | **Semrush** | sending mail, owning contact data |
| Contact/lead/customer data | **Postgres** | — (everything mirrors from here) |
| Content/pages | **Storyblok** | contact data, sending mail |

## Boundary rules

1. **No campaign from Resend/Mailgun.** Anything with a list, segment, or multi-step sequence → Brevo.
2. **No receipt from Brevo.** System-triggered 1:1 messages → Resend, failover Mailgun on 5xx only.
3. **Review-request flow is split by leg, never duplicated:**
   - initial "thanks + review link" transactional email → Resend
   - SMS leg → GatewayAPI
   - delayed nurture email leg → Brevo
   Each system fires exactly one leg.
4. **Semrush sends no mail and stores no contacts.** It is read/analyze/recommend for organic + local.
   - Outbound review *requests* = GatewayAPI/Brevo (yours)
   - Inbound review *monitoring* = Semrush → synced to Postgres `reviews` (see n8n WF-5)
5. **Brevo is a mirror.** Backend upserts contacts INTO Brevo. Brevo never writes back to Postgres
   except via webhook events (opens/clicks/unsubscribes) which update consent/engagement only.

## Quick decision guide

- "Should this email go through Brevo or Resend?" → Does it have a list/segment/sequence? Brevo. Is it a 1:1 system message? Resend.
- "Where do reviews live?" → Postgres `reviews` (system of record). Semrush monitors and feeds it. GBP is the public surface.
- "Who owns rank/listings?" → Semrush, exclusively. No other system touches SEO ops.
