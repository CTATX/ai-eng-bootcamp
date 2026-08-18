# AutoZyte

**Parent product** for licensed shop operations. Not a ShopMonkey reskin.

| Module | Path in repo | Role |
|--------|--------------|------|
| Shop | `shop/` | History warehouse, ShopMonkey ingest, trends, Jake UI |
| FerdAI | `ferdai/` | AI layer — hypothesis, orchestrator (Powered by FerdAI) |
| ZyteShelf | `zyteshelf/` | Inventory — ZyteShelf, ZyteBin, ZyteStock, ZyteLedger |
| Zyren | `zyren/` | AR companion (holding) |

## Repo

https://github.com/BadLabz/autozyte

## Run locally

```bash
git clone https://github.com/BadLabz/autozyte.git
cd autozyte
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add SHOPMONKEY_API_KEY when ready
./start.sh
```

## Docs (in repo)

- `docs/autozyte-product-hierarchy.md` — naming locks
- `docs/shop-intelligence-jtbd.md` — requirements
- `docs/shop-intelligence-plan.md` — P0–P7 build order

## Bootcamp (separate org)

Prototype started in [CTATX/ai-eng-bootcamp](https://github.com/CTATX/ai-eng-bootcamp); production code lives in **BadLabz/autozyte** only.
