# AI Eng Bootcamp

TAI Labs Week 1 build: **FastAPI server** + **Streamlit client** — cost estimation and Q&A.

**Shop / AutoZyte production code** moved to [`autozyte/`](autozyte/) (target repo: [GTInternational/autozyte](https://github.com/GTInternational/autozyte)).

Hub: [GTInternational/Projects](https://github.com/GTInternational/Projects)

## What this repo is

| Piece | Role |
|-------|------|
| `server/` | FastAPI — `GET /health`, `POST /estimate`, `POST /ask` |
| `pages/1_Cost_Estimator.py` | Streamlit cost estimator |
| `pages/2_Bootcamp_QA.py` | Streamlit Q&A |
| `autozyte/` | **AutoZyte product** (split tree — push to GTInternational/autozyte) |
| `docs/ai-eng-bootcamp-playbook.md` | Runbook |

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# OPENAI_API_KEY for /ask only
```

## Run

```bash
./start.sh
```

## AutoZyte (shop platform)

```bash
cd autozyte && ./start.sh
```

See [`autozyte/README.md`](autozyte/README.md).

## TeamOS

`Use TeamOS Bootcamp for [topic]` · [`docs/ai-eng-bootcamp-playbook.md`](docs/ai-eng-bootcamp-playbook.md)
