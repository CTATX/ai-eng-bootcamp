# AI Eng Bootcamp

TAI Labs Week 1 build: **FastAPI server** + **Streamlit client** — cost estimation and Q&A over HTTP.

## What this is

| Piece | Role |
|-------|------|
| `server/` | FastAPI — `GET /health`, `POST /estimate`, `POST /ask` |
| `app.py` | Streamlit cost estimator → calls `/estimate` |
| `pages/2_Bootcamp_QA.py` | Streamlit Q&A → calls `/ask` |
| `docs/ai-eng-bootcamp-playbook.md` | Runbook, troubleshooting, architecture (TeamOS) |

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

**Terminal 1 — server:**
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
