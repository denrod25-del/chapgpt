# SECTION 15 — Environment Variables

Canonical file: **`backend/.env.example`** (updated with the full set — copy to `.env`, fill
keys). Boot-required vars (fail-fast in `config.validate()`): `DATABASE_URL`,
`RESEND_API_KEY`, `GATEWAYAPI_TOKEN`, `OWNER_ALERT_PHONE`.

Vars marked `(v1)` in the file are consumed by blueprint code (idempotency, inbox webhooks,
internal auth, CORS/rate-limit middleware) — add them to `app/config.py` as those pieces land
(Section 7 lists the config additions).

Handling notes:
- Never commit `.env` (already gitignored). In production, inject via Coolify secrets.
- `MAILGUN_API_KEY` doubles as the Mailgun webhook HMAC key — rotating it breaks webhook
  verification until the Mailgun route is updated too.
- `GATEWAYAPI_WEBHOOK_SECRET` / `BREVO_WEBHOOK_TOKEN` exist because those providers don't sign
  payloads — the secret lives in the URL registered with the provider; rotate by registering
  the new URL, then removing the old.
- `INTERNAL_API_TOKEN`: generate with `openssl rand -hex 32`; shared with n8n as a credential.
- n8n additionally needs its own copies of: Postgres DSN, `GATEWAYAPI_TOKEN`,
  `RESEND_API_KEY`, `BREVO_API_KEY`, `OWNER_ALERT_PHONE`, `REVIEW_SHORTLINK_BASE`,
  `INTERNAL_API_TOKEN` — set as n8n credentials/variables, mapped at import (`REPLACE_*`).
