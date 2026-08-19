# Published experiences

## Ownership map

| Product | Home | Notes |
|---------|------|-------|
| **Cost Estimator** | [CTATX/ai-build-crew](https://github.com/CTATX/ai-build-crew) | Canonical — PM + Eng courses merge here |
| **AI Eng Bootcamp** (this repo) | [CTATX/ai-eng-bootcamp](https://github.com/CTATX/ai-eng-bootcamp) | Training demo only |
| **AutoZyte** | [BadLabz/autozyte](https://github.com/BadLabz/autozyte) | Shop / Jake — separate from Cost Estimator |
| **GT International** | Client | Work *for* them — not the Cost Estimator host |
| **BraveLabz** | Your company | GitHub org still **BadLabz** until rename step |

See [`cost-estimator-home.md`](cost-estimator-home.md).

## AI Eng Bootcamp (this repo — course demo)

| Experience | Local | Source |
|------------|-------|--------|
| Cost Estimator (demo) | http://localhost:8501/Cost_Estimator | `pages/1_Cost_Estimator.py` → thin slice of ai-build-crew |
| Bootcamp Q&A | http://localhost:8501/Bootcamp_QA | `pages/2_Bootcamp_QA.py` |

Screenshots: [`docs/examples/`](examples/)

## AutoZyte (production — separate)

| Experience | Repo |
|------------|------|
| Shop intelligence, Jake Advisor, FerdAI | [BadLabz/autozyte](https://github.com/BadLabz/autozyte) |

Nested `autozyte/` in this folder is transitional; product home is BadLabz. See [`autozyte-split.md`](autozyte-split.md).

## Run bootcamp demo

```bash
./start.sh
```

Q&A needs `OPENAI_API_KEY` in `.env`.

## Run Cost Estimator (product)

```bash
cd ~/ai-build-crew
pnpm install && pnpm dev
# http://localhost:3000
```

## Run AutoZyte

```bash
cd ~/autozyte   # or BadLabz/autozyte clone
./start.sh
```
