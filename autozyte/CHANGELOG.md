# Changelog

All notable changes to **BadLabz/autozyte** are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).  
Versioning follows [Semantic Versioning](https://semver.org/) (`0.x` while P0–P2).

Release manifests (full audit trail): [`docs/releases/`](docs/releases/).

## [0.2.0] - 2026-08-18

### Added

- `python -m shop.cli ingest-ticket <RO#>` — pull one ShopMonkey work order by ticket number, enrich vehicle/services, optionally load that vehicle's full order history.
- `python -m shop.cli ingest-order <uuid>` — pull one order by ShopMonkey API id.
- ShopMonkey client: `find_orders_by_number`, `lookup_vehicle_by_vin`, `list_vehicle_orders`, `where` filter on `list_orders`.
- Auto backfill: hypothesis (CLI + API) tries ShopMonkey when a VIN is missing locally and `SHOPMONKEY_API_KEY` is set.
- **Visual system status** (bootcamp pattern): Streamlit **System Status** page + `GET /shop/system/status` — same payload as CLI; link to FastAPI `/docs` for live calls without terminal.
- Release tracking: `VERSION`, this changelog, `docs/releases/manifest-v0.2.0.md`.

### Fixed

- ShopMonkey bulk ingest: removed invalid `include[...]=true` query params (400 from API).
- Order enrich: always fetch full order, services, and vehicle record so VIN/make/model are not lost on sparse list payloads.
- Vehicle upsert: preserve existing VIN and YMM when re-ingest returns `Unknown` / year `0`.

### Verified

- 12 unit tests passing (`python -m unittest discover -s tests`).

## [0.1.0] - 2026-08-18

### Added

- Initial production split from CTATX/ai-eng-bootcamp: `shop/`, `ferdai/`, `zyteshelf/`, `zyren/`, API, Streamlit UI, synthetic Porsche warehouse.
- ShopMonkey bulk ingest (`python -m shop.cli ingest`), Jake hypothesis (`python -m shop.cli hypothesis`).
- BadLabz/Projects hub index entry.

[0.2.0]: docs/releases/manifest-v0.2.0.md
[0.1.0]: docs/releases/manifest-v0.1.0.md
