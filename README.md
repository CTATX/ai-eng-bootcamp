# AI Eng Bootcamp

TAI Labs / Agentic AI Engineer teaching scaffold: **FastAPI** + **Streamlit** — demo cost estimate + Q&A.

**Cost Estimator product home is not this repo** → [CTATX/ai-build-crew](https://github.com/CTATX/ai-build-crew)  
(See [`docs/cost-estimator-home.md`](docs/cost-estimator-home.md).)

**AutoZyte** (shop / Jake) is separate → [BadLabz/autozyte](https://github.com/BadLabz/autozyte).

## What this repo is

| Piece | Role |
|-------|------|
| `server/` | FastAPI — `GET /health`, `POST /estimate`, `POST /ask` |
| `pages/1_Cost_Estimator.py` | **Course demo** of estimate UI (simplified vs ai-build-crew) |
| `pages/2_Bootcamp_QA.py` | Streamlit Q&A |
| `docs/ai-eng-bootcamp-playbook.md` | Runbook |

Nested `autozyte/` / `badlabz-projects/` are transitional copies — not the long-term homes.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# OPENAI_API_KEY for /ask only
```

## Run (bootcamp demo)

```bash
./start.sh
```

## Related repos

| Repo | Role |
|------|------|
| [ai-build-crew](https://github.com/CTATX/ai-build-crew) | **Cost Estimator** (canonical) |
| [BadLabz/autozyte](https://github.com/BadLabz/autozyte) | Shop platform |
| [BadLabz/Projects](https://github.com/BadLabz/Projects) | Product hub |

## TeamOS

`Use TeamOS Bootcamp for [topic]` · [`docs/ai-eng-bootcamp-playbook.md`](docs/ai-eng-bootcamp-playbook.md)
