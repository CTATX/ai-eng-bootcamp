# AI Eng Bootcamp Playbook

**Version:** 1.0 · **Repo:** `ai-eng-bootcamp` · **Invoke:** `Use TeamOS Bootcamp for [topic]`

TAI Labs Week 1 learning artifact. Load this doc on demand — do not paste into every session.

---

## Table of contents

1. [One-breath summary](#1-one-breath-summary)
2. [Architecture map](#2-architecture-map)
3. [File lookup](#3-file-lookup)
4. [Runbook — start everything](#4-runbook--start-everything)
5. [Runbook — restart without closing terminal](#5-runbook--restart-without-closing-terminal)
6. [API endpoints](#6-api-endpoints)
7. [Build steps A–E (checklist)](#7-build-steps-ae-checklist)
8. [Troubleshooting](#8-troubleshooting)
9. [Secrets and `.env`](#9-secrets-and-env)
10. [Concepts glossary](#10-concepts-glossary)
11. [Tie to ai-build-crew](#11-tie-to-ai-build-crew)
12. [Demo script](#12-demo-script)
13. [Shop intelligence (plan)](#13-shop-intelligence-plan)

---

## 1. One-breath summary

**Streamlit = client (UI). FastAPI = server (API). JSON = contract.**

Two terminals run at once: uvicorn (port 8000) + Streamlit (port 8501). Streamlit calls the server over HTTP; only the server talks to OpenAI or runs cost math.

---

## 2. Architecture map

```text
Browser / curl
      │
      ▼
┌─────────────────────────────────────┐
│  Streamlit (client)                 │
│  app.py          → POST /estimate   │
│  pages/2_*       → POST /ask        │
└─────────────────────────────────────┘
      │ HTTP JSON
      ▼
┌─────────────────────────────────────┐
│  FastAPI (server)  :8000            │
│  GET  /health                       │
│  POST /estimate  → cost_engine.py   │
│  POST /ask       → OpenAI API       │
└─────────────────────────────────────┘
```

| Layer | Job | Pays OpenAI tokens? |
|-------|-----|---------------------|
| Streamlit | Display + send requests | No |
| `/estimate` | Deterministic cost math | No |
| `/ask` | Live model Q&A | Yes |

---

## 3. File lookup

| File | Role |
|------|------|
| `app.py` | Cost Estimator UI → calls `/estimate` |
| `pages/2_Bootcamp_QA.py` | Q&A UI → calls `/ask` |
| `api_client.py` | Shared `server_is_up()` + `API_BASE` |
| `server/main.py` | Routes: `/health`, `/estimate`, `/ask` |
| `server/schemas.py` | JSON contracts (request/response shapes) |
| `server/estimate_service.py` | Glue for `/estimate` |
| `server/openai_client.py` | Glue for `/ask` → OpenAI |
| `cost_engine.py` | Cost math + `models.json` catalog |
| `start.sh` | One-command boot: API + Streamlit |
| `.env` | `OPENAI_API_KEY` (server only, gitignored) |
| `CLAUDE.md` | Project index for agents |
| `.claude/agents/ai-eng-bootcamp-agent.md` | TeamOS agent stub |
| `docs/shop-intelligence-plan.md` | Licensed ShopMonkey shop-intel phases P0–P7 |
| `docs/shop-intelligence-briefing.schema.json` | Chat briefing contract (FACT / INFERRED / UNKNOWN) |

---

## 4. Runbook — start everything

### First time (once per machine / fresh clone)

```bash
cd /Users/ctansted/ai-eng-bootcamp
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env — set OPENAI_API_KEY=sk-proj-...
```

### Every session — one command (recommended)

```bash
cd /Users/ctansted/ai-eng-bootcamp
./start.sh
```

Starts the API server (background) + Streamlit (foreground). **Ctrl+C** stops both.

### Every session — two terminals (manual)

**Terminal 1 — server:**

```bash
cd /Users/ctansted/ai-eng-bootcamp
source .venv/bin/activate
uvicorn server.main:app --reload
```

Leave open. Expect: `Uvicorn running on http://127.0.0.1:8000`

**Terminal 2 — client:**

```bash
cd /Users/ctansted/ai-eng-bootcamp
source .venv/bin/activate
streamlit run app.py
```

Use sidebar: **Cost Estimator** | **Bootcamp Q&A**

### Verify without browser

```bash
curl http://127.0.0.1:8000/health
curl -X POST http://127.0.0.1:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"What is an API?"}'
```

Interactive docs (server must be running): http://127.0.0.1:8000/docs

---

## 5. Runbook — restart without closing terminal

| Goal | Action |
|------|--------|
| Stop server or Streamlit | Click in that terminal → **Ctrl+C** → prompt returns |
| Restart same app | Run the same command again in **same tab** |
| New second terminal | Terminal panel → **+** or **Terminal → New Terminal** |
| Clear screen | `clear` or **Cmd+K** |
| Hard close tab | Avoid — kills process; use **Ctrl+C** instead |

**Check venv active:** prompt shows `(.venv)`

**Check correct uvicorn:**

```bash
which uvicorn
# Good: .../ai-eng-bootcamp/.venv/bin/uvicorn
```

If `(.venv)` missing:

```bash
source .venv/bin/activate
```

---

## 6. API endpoints

| Method | Path | Body | Response |
|--------|------|------|----------|
| GET | `/health` | — | `{"status":"ok"}` |
| POST | `/estimate` | `input_tokens`, `result_shape`, `primary_steps`, `checker_steps`, `tasks_per_day` | `recommendation`, `likely_comparison`, `scenario_ranges` |
| POST | `/ask` | `{"question":"..."}` | `{"answer":"...","confidence":0.85}` |

**Contract** = shapes in `server/schemas.py`. Invalid input → rejected before logic runs.

---

## 7. Build steps A–E (checklist)

| Step | What | Status |
|------|------|--------|
| **A** | `GET /health` — server alive | ✅ |
| **B** | `POST /ask` stub — JSON contract | ✅ |
| **C** | OpenAI in `/ask` via `.env` | ✅ |
| **D** | `curl` test `/ask` | ✅ |
| **E** | Streamlit client → API | ✅ |
| **Tie-back** | `POST /estimate` + first app calls API | ✅ |
| **Next** | Docker + deploy to public URL | See [deploy-render.md](deploy-render.md) |

---

## 8. Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `ERR_CONNECTION_REFUSED` on `:8000` | Server not running | Start uvicorn (Terminal 1) |
| `Address already in use` | Old uvicorn still on 8000 | `lsof -i :8000` → `kill <PID>` → restart |
| `ModuleNotFoundError: dotenv` | Wrong Python / venv off | `source .venv/bin/activate` + `pip install -r requirements.txt` |
| `OPENAI_API_KEY is missing` | Empty or malformed `.env` | See [§9 Secrets](#9-secrets-and-env) |
| `401 Invalid API key` | Cursor key (`sk-crsr-`) or wrong key | Use key from platform.openai.com |
| `402` / no credits | OpenAI billing empty | Add credits at platform.openai.com billing |
| Streamlit "API not running" | uvicorn stopped | Restart Terminal 1 |
| `/docs` blank / refused | Same as connection refused | Server must be running first |

**Streamlit email prompt (first run):** leave blank → Enter. Optional signup only.

---

## 9. Secrets and `.env`

**Format (equals sign required):**

```text
OPENAI_API_KEY=sk-proj-your-key-here
```

| ❌ Wrong | ✅ Right |
|---------|----------|
| `OPENAI_API_KEYsk-proj-...` | `OPENAI_API_KEY=sk-proj-...` |
| Cursor key `sk-crsr-...` | OpenAI key from platform.openai.com |
| Key in GitHub / chat | Key in `.env` only |

After editing `.env`: **Ctrl+C** server → restart uvicorn.

---

## 10. Concepts glossary

| Term | Plain English |
|------|----------------|
| **Client** | Caller — Streamlit, curl, browser |
| **Server** | Listener — FastAPI on port 8000 |
| **API** | Agreed menu of URLs + JSON shapes |
| **Contract** | `schemas.py` — what must be sent/received |
| **Endpoint** | One menu item (e.g. `POST /ask`) |
| **Scaffold** | Smallest working slice before features |
| **venv** | Isolated Python packages for this project |
| **uvicorn** | Process that runs the FastAPI server |
| **POST** | Send data to run something (has a body) |
| **GET** | Read something (safe, no body) |

---

## 11. Tie to ai-build-crew

| Bootcamp | ai-build-crew |
|----------|---------------|
| `POST /estimate` | Deterministic cost specialist (no model tokens) |
| `POST /ask` | Live model path (explicit spend) |
| `cost_engine.py` | Simplified cost method + catalog |
| Streamlit client | Product UI calling your API |
| Week 1 local server | Deployed TS/React product |

Same product thinking; bootcamp = Python learning scaffold; ai-build-crew = production shape.

---

## 12. Demo script

1. Terminal 1: `uvicorn server.main:app --reload`
2. `curl http://127.0.0.1:8000/health` → ok
3. Terminal 2: `streamlit run app.py`
4. **Cost Estimator** → Estimate → shows API-connected recommendation
5. **Bootcamp Q&A** → ask "What is RAG?" → real answer
6. Browser: `http://127.0.0.1:8000/docs` → show contract

**One-liner:** "I built a FastAPI service with two endpoints; Streamlit is a thin client."

---

## 13. Shop intelligence (plan)

Licensed shop owner using ShopMonkey’s **official API** for internal analysis. Not a reskin.

- Plan: [`docs/shop-intelligence-plan.md`](shop-intelligence-plan.md)
- Briefing contract: [`docs/shop-intelligence-briefing.schema.json`](shop-intelligence-briefing.schema.json)

**Next code is P1 (warehouse ingest) only.** Chat and multi-agent stay parked until facts exist.

---

## Syllabus links

- [Software components for beginners](https://tailabs.ai/ai-eng-syllabus/pre-course/software-components-for-beginners/)
- [Session 1 checklist](https://tailabs.ai/ai-eng-syllabus/pre-course/session-1-checklist/)
