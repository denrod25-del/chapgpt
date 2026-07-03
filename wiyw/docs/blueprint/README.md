# WiYW Backend & Automation Blueprint — Handoff Package

Implementation blueprint for the plumbing-brand marketing stack (FastAPI + Postgres + n8n +
Brevo/Resend/Mailgun/GatewayAPI). One brand today (**What's in Your Water**, Palm Beach County FL);
multi-brand-compatible schema for productization later.

**How this relates to the built system:** `backend/` is boot-tested and canonical — this blueprint
documents it, extends it (migration `005_platform_entities.sql`, verified up/down/up against live
Postgres 16), and specifies everything not yet built. Where the blueprint and code disagree, the
code + migrations win; file an issue.

## Sections

| # | File | Contents |
|---|------|----------|
| 1 | [01_architecture.md](01_architecture.md) | System boundaries, source of truth, ownership, event-driven summary |
| 2 | [02_repository_structure.md](02_repository_structure.md) | Project structure, folder purposes |
| 3 | [03_data_model.md](03_data_model.md) | Table-by-table Postgres data model + conventions |
| 4 | [04_sql_ddl.md](04_sql_ddl.md) | SQL DDL (pointer to migrations 001–005 + consolidated notes) |
| 5 | [05_pydantic_models.md](05_pydantic_models.md) | Request/response Pydantic models |
| 6 | [06_route_map.md](06_route_map.md) | Full FastAPI route map (`/api/v1`) |
| 7 | [07_code_scaffold.md](07_code_scaffold.md) | Code skeletons: layering, webhooks, background tasks, clients |
| 8 | [08_webhook_design.md](08_webhook_design.md) | Per-provider webhook design (verify → store raw → 200 → async) |
| 9 | [09_event_taxonomy.md](09_event_taxonomy.md) | Canonical event taxonomy with payloads + retention |
| 10 | [10_brevo_contract.md](10_brevo_contract.md) | Brevo integration contract (extends docs/BREVO_SETUP.md) |
| 11 | [11_email_sms_split.md](11_email_sms_split.md) | Brevo/Resend/Mailgun/GatewayAPI decision table |
| 12 | [12_n8n_workflows.md](12_n8n_workflows.md) | 8 workflow specs |
| 13 | [13_n8n_node_outlines.md](13_n8n_node_outlines.md) | Node-by-node outlines for all 8 |
| 14 | [14_api_contracts.md](14_api_contracts.md) | Concrete JSON request/response examples |
| 15 | [15_env_example.md](15_env_example.md) | Environment variables (mirrors backend/.env.example) |
| 16 | [16_naming_conventions.md](16_naming_conventions.md) | Naming conventions across all systems |
| 17 | [17_sprint_plan.md](17_sprint_plan.md) | First 7-day build order |

`scaffolds/` contains liftable code for the pieces the backend doesn't have yet
(webhooks inbox pattern, idempotency dependency).

## Real inputs still needed (placeholders marked `⟨…⟩` throughout)

| Placeholder | Value |
|-------------|-------|
| BRAND_NAME | What's in Your Water ✅ (seeded in `brands`) |
| PRIMARY_CITY / STATE | West Palm Beach / FL ✅ |
| WEBSITE_DOMAIN | whatsinyourwater.com ✅ |
| DEFAULT_FROM_EMAIL | ⟨hello@mail.whatsinyourwater.com — confirm after Resend domain verify⟩ |
| MAIN_PHONE | ⟨insert E.164⟩ → `BRAND_PHONE` env + `brands.main_phone` |
| PRIMARY_BOOKING_URL | ⟨insert⟩ → `brands.booking_url` |
| GBP_REVIEW_URL | ⟨insert⟩ → `brands.gbp_review_url` + `REVIEW_SHORTLINK_BASE` |
| CMS_PLATFORM | Storyblok ✅ (chosen; components built) |
| DATABASE_URL | ⟨insert⟩ |
| BREVO_LIST_NEW_LEADS / CUSTOMERS / REVIEW_REQUESTS | list IDs 2 / 3 / (segment) per docs/BREVO_SETUP.md — ⟨confirm IDs after account setup⟩ |
