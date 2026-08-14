# AI Eng Bootcamp

TAI Labs build: **FastAPI server** + **Streamlit client** — planning, Q&A, outcome-linked AI FinOps, and a ShopMonkey shop integration.

## What this is

| Piece | Role |
|-------|------|
| `server/` | FastAPI — health, estimate, ask, FinOps, and ShopMonkey endpoints |
| `app.py` | Streamlit multipage home |
| `pages/1_Cost_Estimator.py` | Planning estimator → calls `/estimate` |
| `pages/2_Bootcamp_QA.py` | Streamlit Q&A → calls `/ask` |
| `pages/3_AI_FinOps.py` | Actual usage, outcomes, attribution, and budget status |
| `pages/4_ShopMonkey.py` | Official ShopMonkey REST integration (not a reskin) |
| `docs/ai-finops-kpi-contract.md` | KPI definitions, confidence, and governance controls |
| `docs/shopmonkey-api-contract.md` | Allowed vs blocked ShopMonkey API use |
| `docs/ai-eng-bootcamp-playbook.md` | Runbook, troubleshooting, architecture (TeamOS) |

Related: [ai-build-crew](https://github.com/CTATX/ai-build-crew) (production cost planner).

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env — OPENAI_API_KEY=sk-proj-... (for /ask)
# Optional: SHOPMONKEY_API_KEY=... (for live shop data)
```

## Run (two terminals)

**Easy — one command:**
```bash
./start.sh
```

**Manual — Terminal 1 (server):**
```bash
uvicorn server.main:app --reload
```

**Terminal 2 — client:**
```bash
streamlit run app.py
```

- API docs: http://127.0.0.1:8000/docs  
- Streamlit: http://localhost:8501  

## AI FinOps MVP

Every successful `/ask` call now records provider-reported token usage, an estimated cost,
attribution tags, latency, and a pending outcome review in local SQLite. The dashboard shows:

- 7/30-day and average daily spend
- provider-reported cache ratio
- successful-task and acceptance rates
- cost per accepted outcome
- spend by business owner, user, use case, or model
- daily budget status and optional hard stop

Cost is estimated from configured pricing and is not yet reconciled to provider invoices.
The Render free-tier database is ephemeral; production persistence requires Postgres.

## ShopMonkey integration

Official REST v3 only. Our UI reads shop data; we do not reskin or white-label ShopMonkey.

- Catalog (no key): `GET /shopmonkey/catalog`
- Live snapshot: `GET /shopmonkey/snapshot` after `SHOPMONKEY_API_KEY` is set
- Contract: [`docs/shopmonkey-api-contract.md`](docs/shopmonkey-api-contract.md)

## TeamOS

Invoke in Cursor/Claude: **`Use TeamOS Bootcamp for [topic]`**  
Full runbook: [`docs/ai-eng-bootcamp-playbook.md`](docs/ai-eng-bootcamp-playbook.md)

## Syllabus

- [Software components for beginners](https://tailabs.ai/ai-eng-syllabus/pre-course/software-components-for-beginners/)
- [Session 1 checklist](https://tailabs.ai/ai-eng-syllabus/pre-course/session-1-checklist/)
