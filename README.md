# AI Eng Bootcamp

TAI Labs Week 1 build: **FastAPI server** + **Streamlit client** — cost estimation, Q&A, and a synthetic Porsche shop-intelligence prototype.

## Experiences (open these on GitHub)

**Full path list + screenshots:** [docs/experiences.md](https://github.com/CTATX/ai-eng-bootcamp/blob/cursor/shop-intelligence-plan-11ee/docs/experiences.md)

| Experience | Screenshot |
|------------|------------|
| Cost Estimator | [image](https://github.com/CTATX/ai-eng-bootcamp/blob/cursor/shop-intelligence-plan-11ee/docs/examples/cost-estimator.png) |
| Bootcamp Q&A | [image](https://github.com/CTATX/ai-eng-bootcamp/blob/cursor/shop-intelligence-plan-11ee/docs/examples/bootcamp-qa.png) |
| Shop intelligence — Trends | [image](https://github.com/CTATX/ai-eng-bootcamp/blob/cursor/shop-intelligence-plan-11ee/docs/examples/shop-intel-trends.png) |
| Shop intelligence — Product list | [image](https://github.com/CTATX/ai-eng-bootcamp/blob/cursor/shop-intelligence-plan-11ee/docs/examples/shop-intel-parts.png) |
| Shop intelligence — Job packet holes | [image](https://github.com/CTATX/ai-eng-bootcamp/blob/cursor/shop-intelligence-plan-11ee/docs/examples/shop-intel-packets.png) |

PR: https://github.com/CTATX/ai-eng-bootcamp/pull/2

## What this is

| Piece | Role |
|-------|------|
| `server/` | FastAPI — `GET /health`, `POST /estimate`, `POST /ask` |
| `app.py` | Streamlit cost estimator → calls `/estimate` |
| `pages/2_Bootcamp_QA.py` | Streamlit Q&A → calls `/ask` |
| `docs/ai-eng-bootcamp-playbook.md` | Runbook, troubleshooting, architecture (TeamOS) |
| `docs/shop-intelligence-jtbd.md` | Running JTBD + requirements (rough cut) |
| `docs/shop-intelligence-plan.md` | ShopMonkey shop-intel plan (licensed shop, no reskin) |
| `pages/3_Shop_Intelligence.py` | Synthetic Porsche trends + product list |

Related: [ai-build-crew](https://github.com/CTATX/ai-build-crew) (production cost planner).

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env — OPENAI_API_KEY=sk-proj-... (for /ask only)
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

## TeamOS

Invoke in Cursor/Claude: **`Use TeamOS Bootcamp for [topic]`**  
Full runbook: [`docs/ai-eng-bootcamp-playbook.md`](docs/ai-eng-bootcamp-playbook.md)

## Syllabus

- [Software components for beginners](https://tailabs.ai/ai-eng-syllabus/pre-course/software-components-for-beginners/)
- [Session 1 checklist](https://tailabs.ai/ai-eng-syllabus/pre-course/session-1-checklist/)
