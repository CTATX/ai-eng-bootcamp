# AI Eng Bootcamp

TAI Labs Week 1 build: **FastAPI server** + **Streamlit client** — cost estimation and Q&A.

**Shop / AutoZyte production code** moved to [`autozyte/`](autozyte/) → [BadLabz/autozyte](https://github.com/BadLabz/autozyte).

Hub: [BadLabz/Projects](https://github.com/BadLabz/Projects) · Org: [BadLabz](https://github.com/BadLabz)

## What this repo is

| Piece | Role |
|-------|------|
| `server/` | FastAPI — `GET /health`, `POST /estimate`, `POST /ask` |
| `pages/1_Cost_Estimator.py` | Streamlit cost estimator |
| `pages/2_Bootcamp_QA.py` | Streamlit Q&A |
| `autozyte/` | **AutoZyte product** — push to BadLabz/autozyte |
| `badlabz-projects/` | **Projects hub** — push to BadLabz/Projects |
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
