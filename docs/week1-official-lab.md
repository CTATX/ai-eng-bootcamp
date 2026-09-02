# Week 1 — Official lab (foundation lock)

**Cohort source:** [AI-Internship week-1](https://github.com/akshika47/AI-Internship/tree/main/ai-engineering-bootcamp-v2/week-1)

**Why:** Your `ai-eng-bootcamp` repo proves the **outcome**. This lab proves you understand **each layer** the cohort builds on.

**Finish line:** `python test_all_stages.py` passes → foundation locked → OK to move toward Week 2.

**Time box:** ~2 hours total, or **one stage per sitting** (ADHD-safe).

---

## Coach phrases (same as Week 1)

| You say | What happens |
|---------|----------------|
| **Coach me through official stage N** | One stage only |
| **done** / **stuck** | Update progress below |

---

## Progress

- [x] **Setup** — clone repo, copy `.env` key, venv, deps
- [x] **Stage 1** — `serve_stage1.py` — bare `/ask`, tokens
- [x] **Stage 2** — `serve_stage2.py` — Pydantic structured output
- [x] **Stage 3** — `serve_stage3.py` — validation + retry
- [x] **Stage 4** — `serve_stage4.py` — model override + latency
- [x] **Stage 5** — `serve_stage5.py` / `main.py` — cost readout
- [x] **Streamlit** — `demo_page.py` hits a stage successfully ✅ **2026-08-28**
- [x] **Smoke test** — `python test_all_stages.py` all green ✅ **2026-08-28**
- [x] **Foundation locked** 🎯

---

## Setup (once)

```bash
cd ~
git clone https://github.com/akshika47/AI-Internship.git
cd AI-Internship/ai-engineering-bootcamp-v2/week-1
cp .env.example .env
# same OPENAI_API_KEY as ai-eng-bootcamp — never paste in chat
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

**Port rule:** Stop `./start.sh` in `ai-eng-bootcamp` first — both use **8000**.

---

## Extra rep — `demo_page.py` (Streamlit UI)

**Where this lives:** `docs/week1-official-lab.md` (this file). Quick link from scorecard in `docs/week1-catchup-checklist.md`.

**Two terminals** — server first, then Streamlit.

**Terminal 1 — API (stage 5 = full build):**

```bash
cd ~/AI-Internship/ai-engineering-bootcamp-v2/week-1
source .venv/bin/activate
uvicorn serve_stage5:app --host 127.0.0.1 --port 8000 --reload
```

**Terminal 2 — demo UI** (`Ctrl+Shift+` ` for new tab):

```bash
cd ~/AI-Internship/ai-engineering-bootcamp-v2/week-1
source .venv/bin/activate
streamlit run demo_page.py
```

**Browser:** http://localhost:8501 (or the URL Streamlit prints)

| In the UI | Set / do |
|-----------|----------|
| Sidebar **API base URL** | `http://127.0.0.1:8000` |
| Tab **Demo 5: Cost readout** | Pick question → **Run test** |
| Success | JSON with `cost_usd`, `latency_ms`, structured `answer` |

**`/docs` Try it out tip:** Do **not** leave `"model": "string"` — that's a Swagger placeholder. Use `"gpt-4o-mini"` or omit `model`.

**404 on `GET /`:** Normal — this lab only has `POST /ask` and `/docs`.

---

## Per-stage loop (repeat 1→5)

**Terminal 1:**

```bash
cd ~/AI-Internship/ai-engineering-bootcamp-v2/week-1
source .venv/bin/activate
uvicorn serve_stageN:app --host 127.0.0.1 --port 8000 --reload
```

**Terminal 2 (optional UI — full path required):**

```bash
cd ~/AI-Internship/ai-engineering-bootcamp-v2/week-1
source .venv/bin/activate
streamlit run demo_page.py
```

See **Extra rep — demo_page.py** above for the two-terminal flow.

**Terminal 2 (curl):**

```bash
curl -s -X POST http://127.0.0.1:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is RAG in one sentence?"}'
```

Replace `serve_stageN` with `serve_stage1`, `serve_stage2`, … `serve_stage5`.

---

## Map: your repo vs official stages

| Stage | Official teaches | Your `ai-eng-bootcamp` |
|-------|------------------|-------------------------|
| 1 | Minimal `/ask` | ✅ Done — but read their file anyway |
| 2 | Pydantic parse | ✅ `schemas.py` — compare shapes |
| 3 | Retry guardrail | ⚠️ Read carefully — may differ |
| 4 | Per-request `model` | ⚠️ Compare to your fixed model |
| 5 | `cost_usd` on response | Partial — you have `/estimate` separately |

**Goal isn't duplicate code** — it's **see each increment** so Week 2+ clicks.

---

## When foundation is locked

Update `docs/week1-catchup-checklist.md` mentally: **Week 1 outcome + official stages complete.**

Then say: **Coach me through Week 2** (when cohort material is ready).

---

## ADHD rule

- **One stage = one win.** Stop after smoke test passes for that stage.
- **Don't** merge official repo into `ai-eng-bootcamp` — separate folder, separate terminal.
- **Do** celebrate each stage — same rush as `/docs` and `/ask`.
