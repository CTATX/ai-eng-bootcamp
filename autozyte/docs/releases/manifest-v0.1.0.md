# Release manifest — AutoZyte v0.1.0

| Field | Value |
|-------|--------|
| **Version** | 0.1.0 |
| **Date** | 2026-08-18 |
| **Repo** | [BadLabz/autozyte](https://github.com/BadLabz/autozyte) |
| **Status** | Initial production split |
| **Source** | CTATX/ai-eng-bootcamp — AutoZyte product tree |

## Summary

First publish of AutoZyte as a standalone BadLabz product repo: shop warehouse, synthetic seed, Jake hypothesis (FerdAI), Streamlit + FastAPI, ShopMonkey ingest scaffold.

## Scope

- Modules: `shop/`, `ferdai/`, `zyteshelf/` (stub), `zyren/` (stub)
- CLI: `status`, `ingest`, `hypothesis`
- UI: Shop Intelligence, Jake Advisor
- Docs: product hierarchy, JTBD, P0–P7 plan

## Not in this release

- Live ShopMonkey ticket pull by RO number
- Order-per-fetch enrich (list API often sparse)
- Release manifest process (added in v0.2.0)

## Publish

Published via `./scripts/publish-to-github.sh` from ai-eng-bootcamp workspace with `gh auth login` (BadLabz org owner).
