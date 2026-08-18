# AutoZyte

Licensed shop operations platform for GT International. **Not a ShopMonkey reskin.**

| Module | Role |
|--------|------|
| **shop/** | History warehouse, ShopMonkey ingest, trends UI |
| **ferdai/** | AI layer — advisor hypothesis (Powered by FerdAI) |
| **zyteshelf/** | Inventory — ZyteShelf, ZyteBin, ZyteStock, ZyteLedger |
| **zyren/** | AR companion (holding) |

Hub: [BadLabz/Projects](https://github.com/BadLabz/Projects)

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## Run

```bash
chmod +x start.sh
./start.sh
```

- API: http://127.0.0.1:8000/docs  
- Streamlit: http://localhost:8501  

## CLI

```bash
python -m shop.cli status
python -m shop.cli hypothesis --vin SYNWP020140002 --complaint "AOS" --compact
python -m shop.cli ingest --max-pages 5   # requires SHOPMONKEY_API_KEY
python -m shop.cli ingest-ticket 1042     # pull one RO + that car's history
```

**Release:** see [`CHANGELOG.md`](CHANGELOG.md) and [`docs/releases/`](docs/releases/) (current: `VERSION` file).

## Docs

- [Product hierarchy](docs/autozyte-product-hierarchy.md)
- [Shop JTBD](docs/shop-intelligence-jtbd.md)
- [Plan P0–P7](docs/shop-intelligence-plan.md)

Teaching scaffold (separate repo): [CTATX/ai-eng-bootcamp](https://github.com/CTATX/ai-eng-bootcamp)
