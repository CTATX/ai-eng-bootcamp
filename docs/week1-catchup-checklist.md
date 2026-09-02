# Week 1 Catch-Up Checklist

**For:** CT catching up while cohort is ahead  
**Repo:** `ai-eng-bootcamp` only  

## How to use (pick one — no memorizing)

| You say | What happens |
|---------|----------------|
| **Coach me through Week 1** | Agent walks you step by step |
| **What's next?** | Agent reads progress, gives one step |
| **done** / **stuck** | Agent updates `docs/week1-progress.md` and continues |

Progress tracker (agent-maintained): **`docs/week1-progress.md`**

One box at a time. Do not open other repos in this session.

---

## Week 1 scorecard (single source of truth)

**Status: COMPLETE — 2026-08-28**

| Track | Required | Your status |
|-------|----------|-------------|
| **A — Your repo** (`ai-eng-bootcamp`) | Steps 0–9 in checklist below | ✅ **9/9** |
| **B — Cohort lab** (`AI-Internship/week-1`) | Setup + stages 1–5 via smoke test | ✅ **5/5 stages** |
| **B — Optional** | `demo_page.py` Streamlit — see **`docs/week1-official-lab.md`** § Extra rep | ✅ **Done** |

**Foundation locked** = Track A complete **and** Track B smoke test 5/5. You have both.

---

## Checklist

- [x] **0 — Workspace** — Cursor folder is `ai-eng-bootcamp`
- [x] **1 — `.env`** — `OPENAI_API_KEY=sk-proj-...` saved (Cmd+S). Key from platform.openai.com
- [x] **2 — One-time setup** (if needed) — `python3 -m venv .venv`, `pip install -r requirements.txt`
- [x] **3 — Start** — `./start.sh` running; note Streamlit URL (8501 or 8502)
- [x] **4 — Health (curl)** — `curl http://127.0.0.1:8000/health` → `{"status":"ok"}`
- [x] **5 — Health (UI)** — Sidebar **API Health** → green status
- [x] **6 — Docs** — Browser: http://127.0.0.1:8000/docs
- [x] **7 — Ask (curl)** — `POST /ask` returns JSON with `answer`
- [x] **8 — Ask (UI)** — Sidebar **Bootcamp Q&A** → ask a question → see answer
- [x] **9 — Done** — You can explain: client (Streamlit) → server (FastAPI) → OpenAI (`/ask` only)

---

## Week 1 complete ✅

**Completed:** 2026-08-28

| Layer | Your words | + one precision |
|-------|------------|-----------------|
| **Client** | Streamlit shows you what's going on | It also **sends** requests — UI + caller |
| **Server** | Magic listener, pulse check, keyed through the service | `/health` = pulse; `/ask` = your key → OpenAI; nothing else spends tokens |
| **Contract** | Written agreement for how systems talk | That's `schemas.py` + JSON — e.g. `{"question":"..."}` in, `{"answer":"..."}` out |

*"Are you hosed or not"* = `GET /health`. That's the heartbeat.


## Terminal tip

`./start.sh` **occupies** that terminal tab. For curl, open a **new tab**: **Ctrl+Shift+`**

---

## What "Port 8000 already in use" means

API is already running from an earlier start. That's fine if `curl /health` returns ok.

---

## Week 1 complete → what's next

**Outcome + official lab:** locked 2026-08-28 (`test_all_stages.py` 5/5). See `docs/week1-official-lab.md`.

Stop here for today unless you're in flow. **Week 2:** `docs/week2-catchup-checklist.md` — say **Coach me through Week 2**.
