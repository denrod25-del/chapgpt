# WF-5 · Semrush Review Monitoring → Postgres (reputation sync)

Purpose: pull inbound reviews Semrush is monitoring (Google/Facebook) into the Postgres
`reviews` table so the **system of record** holds reputation data, and downstream metrics
(review_received events, response tracking) work off one source.

Semrush owns *monitoring*. Postgres owns *storage*. This workflow is the one-way bridge.

## Important: data-source reality
Semrush review data is not exposed as cleanly as Position Tracking. Two supported paths:
- **A (preferred):** Semrush API endpoint for your project's listing/review data, if your
  plan tier includes it. Poll on schedule.
- **B (fallback):** scheduled CSV export from Semrush Listing Management → dropped to a
  location n8n can read (Drive/S3/HTTP), parsed on schedule.

Both converge on the same normalize + upsert logic below. WF-5 JSON implements path A with
an HTTP Request node; swap node 2 for a Read/Parse node to use path B.

## Idempotency (critical)
Monitoring feeds give no stable per-review ID. To avoid duplicate rows on every poll, we
dedup on a deterministic hash of `(platform, rating, content, review_date)`. The DB enforces
this with a UNIQUE index on a generated hash column (see migration 004 below).

## Nodes

| # | Node | Type | Logic |
|---|------|------|-------|
| 1 | Every 6h | Schedule Trigger | cron `0 */6 * * *` |
| 2 | Fetch Semrush reviews | HTTP Request | GET Semrush reviews endpoint (API key, project id). Path B: Read+Parse CSV instead. |
| 3 | Normalize | Code (JS) | map each raw review → {platform, rating, content, review_date, author}; drop rows missing rating or content |
| 4 | Split | Split Out | one item per review |
| 5 | Match customer | Postgres | best-effort: `SELECT id FROM customers WHERE full_name ILIKE $1 LIMIT 1` (author name); null if no match — review still stored |
| 6 | Upsert review | Postgres | compute hash inline, then `INSERT ... ON CONFLICT (dedupe_hash) DO NOTHING` (SQL below) |
| 7 | Emit event (new only) | Postgres | if insert affected a row → INSERT events (event_name='review_received') |
| 8 | Alert on low rating | IF → GatewayAPI | rating <= 3 → SMS owner: "New {rating}★ review needs a response" |

## Fallback logic
- Semrush endpoint 4xx/5xx → log + skip cycle (don't crash; next run retries). Bounded: no retry storm.
- Author name no match → store review with `customer_id = NULL`. Reputation data is not lost.
- Duplicate → `ON CONFLICT DO NOTHING` silently no-ops; event NOT emitted (no double count).

## Metrics to monitor
- New reviews/week by platform
- Average rating trend
- Low-rating (≤3★) response time (owner alert → response logged)
- % reviews matched to a customer (data quality signal)

## Upsert node (node 6) — SQL
The hash is computed in the INSERT using the SAME recipe as migration 004's backfill, so
values written by WF-5 and any backfilled rows collide correctly.
```sql
INSERT INTO reviews (customer_id, rating, platform, content, review_date,
                     external_source, received_at, author, dedupe_hash)
VALUES ($1, $2, $3, $4, $5::date, 'semrush', now(), $6,
        md5( coalesce($3,'') || '|' || coalesce($2::text,'') || '|' ||
             coalesce($4,'') || '|' || coalesce(to_char($5::date,'YYYY-MM-DD'),'') ))
ON CONFLICT (dedupe_hash) DO NOTHING;
```
> Because the hash is built in the VALUES clause (not a stored generated column), it sidesteps
> PG's immutability rule while still deduping deterministically.

## Normalize node (node 3) — reference JS
```javascript
// Bounded, defensive. Returns [] on malformed input rather than throwing.
const items = $input.all();
const out = [];
for (const it of items) {
  const raw = it.json.reviews ?? it.json.data ?? [];
  if (!Array.isArray(raw)) continue;
  for (const r of raw.slice(0, 500)) {          // bound: max 500/cycle
    const rating = Number(r.rating ?? r.stars);
    const content = (r.text ?? r.content ?? '').trim();
    if (!Number.isInteger(rating) || rating < 1 || rating > 5) continue;
    if (!content) continue;
    out.push({ json: {
      platform: (r.platform ?? 'google').toLowerCase(),
      rating,
      content,
      review_date: r.date ?? r.created_at ?? null,
      author: (r.author ?? r.reviewer ?? '').trim() || null,
    }});
  }
}
return out;
```
