# Release manifest — AutoZyte v0.2.0

| Field | Value |
|-------|--------|
| **Version** | 0.2.0 |
| **Date** | 2026-08-18 |
| **Repo** | [BadLabz/autozyte](https://github.com/BadLabz/autozyte) |
| **Status** | Vetted — ready for BadLabz publish |
| **Bootcamp PR** | [CTATX/ai-eng-bootcamp#11](https://github.com/CTATX/ai-eng-bootcamp/pull/11) |
| **Bootcamp branch** | `cursor/vin-ticket-ingest-11ee` |

## Summary

ShopMonkey ingest hardening plus **ticket-based ingest** so a live RO in the shop (with VIN on the ticket) can be pulled into the local warehouse and matched by Jake — without waiting for bulk pagination to reach that order.

## Problem addressed

- Jake reads **local SQLite only** (`SHOP_INTEL_DB_PATH`).
- Bulk ingest stopped after ~50 orders; BMW `WBA3A5C51CF346278` was in ShopMonkey but not in the warehouse → hypothesis returned **UNKNOWN**.
- List-order API responses often lack full vehicle/VIN; prior upserts could overwrite good data with `Unknown` / null VIN.

## Changes

### ShopMonkey client (`shop/shopmonkey_client.py`)

| Change | Detail |
|--------|--------|
| Fix list orders | No `include[customer\|vehicle\|services]=true` (API 400) |
| `find_orders_by_number(ticket)` | `GET /order?where={"number":…}` |
| `lookup_vehicle_by_vin(vin)` | `GET /vehicle/vin/{vin}` |
| `list_vehicle_orders(vehicle_id)` | `GET /vehicle/{id}/order` |
| `list_orders(where=…)` | JSON `where` filter support |

### Ingest (`shop/ingest.py`)

| Change | Detail |
|--------|--------|
| `_enrich_order` | Always fetch full order + services + vehicle when sparse |
| VIN preservation | `COALESCE` on upsert — do not wipe VIN on re-ingest |
| `ingest_order_by_ticket` | RO number → enrich → warehouse + optional vehicle history |
| `ingest_order_by_id` | Single order by UUID |
| `ensure_vehicle_for_vin` | Backfill path for hypothesis |

### CLI / API

| Surface | Change |
|---------|--------|
| `shop.cli ingest-ticket` | New command |
| `shop.cli ingest-order` | New command |
| `GET /shop/system/status` | Same JSON as `shop.cli status` |
| Streamlit **System Status** | Visual health + try-it buttons + `/docs` link |
| `POST /advisor/hypothesis` | Auto backfill when VIN missing + key set |
| `shop.cli hypothesis` | Same backfill |

### Docs

- `VERSION`, `CHANGELOG.md`, this manifest, `docs/releases/README.md`

## Verification (vetted)

```bash
cd autozyte
python -m unittest discover -s tests -q
# Ran 14 tests — OK
```

| Test file | Covers |
|-----------|--------|
| `test_shop_synthetic.py` | Porsche seed |
| `test_shop_ingest.py` | ShopMonkey order mapping |
| `test_shop_hypothesis.py` | Jake VIN match / UNKNOWN |
| `test_shop_ticket_ingest.py` | Ticket ingest + VIN preservation |
| `test_shop_system_status.py` | CLI/API status payload shape |

## Upgrade (after publish)

On your Mac (`~/autozyte`):

```bash
git pull origin main
cat VERSION          # expect 0.2.0
python -m shop.cli ingest-ticket YOUR_RO_NUMBER
python -m shop.cli hypothesis --vin YOUR_VIN --compact
```

## Files touched (this release)

```
VERSION
CHANGELOG.md
README.md
docs/releases/manifest-v0.2.0.md
docs/releases/manifest-v0.1.0.md
docs/releases/README.md
server/main.py
shop/cli.py
shop/system_status.py
shop/ingest.py
shop/shopmonkey_client.py
pages/0_System_Status.py
api_client.py
app.py
tests/test_shop_ticket_ingest.py
tests/test_shop_system_status.py
```

## Out of scope (next)

- GitHub Release asset / Docker tag (P0 syllabus)
- Parts ingest via `/order/:id/part`
- BadLabz/Projects hub dedupe (`projects/autozyte/` code copy)

## Sign-off

| Check | Result |
|-------|--------|
| Unit tests | Pass (14/14) |
| Secrets in repo | None (`.env` gitignored) |
| Manifest present | Yes |
| Semver bump | 0.1.0 → 0.2.0 |
