# Week 1v2 — Official class demo

**Path:** `~/AI-Internship/ai-engineering-bootcamp-v2/week-1v2`  
**README:** [week-1v2 on GitHub](https://github.com/akshika47/AI-Internship/tree/main/ai-engineering-bootcamp-v2/week-1v2)

Pre-course (`ai-eng-bootcamp`) got you here. This is the **main Week 1** the repo points to.

---

## Setup (once)

```bash
cd ~/AI-Internship/ai-engineering-bootcamp-v2/week-1v2
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
test -f .env || cp .env.example .env
# add OPENAI_API_KEY (same as ai-eng-bootcamp — never paste in chat)
```

Copy key from existing `.env`:

```bash
cp ~/ai-eng-bootcamp/.env .env
```

---

## Run (two terminals)

**Terminal 1 — API:**

```bash
cd ~/AI-Internship/ai-engineering-bootcamp-v2/week-1v2
source .venv/bin/activate
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

**Terminal 2 — Streamlit:**

```bash
cd ~/AI-Internship/ai-engineering-bootcamp-v2/week-1v2
source .venv/bin/activate
streamlit run demo_page.py
```

| Check | URL |
|-------|-----|
| Health | http://127.0.0.1:8000/health |
| Docs | http://127.0.0.1:8000/docs |
| UI | http://localhost:8501 |

Stop `./start.sh` in `ai-eng-bootcamp` first if port 8000 is busy.

---

## Finish line (Week 1v2 complete)

```bash
cd ~/AI-Internship/ai-engineering-bootcamp-v2/week-1v2
source .venv/bin/activate
python smoke_test.py
```

Then in Streamlit: ask a question + toggle **Force bad first response** once.

---

## Optional stage files (reference while doing)

```bash
uvicorn stages.stage_1_bare_ask:app --host 127.0.0.1 --port 8000 --reload
uvicorn stages.stage_2_structured_output:app --host 127.0.0.1 --port 8000 --reload
uvicorn stages.stage_3_guardrails_and_observability:app --host 127.0.0.1 --port 8000 --reload
```

Read the file **after** you run it — learn-by-doing.

---

## Swagger tip (from pre-course UAT)

Do **not** submit `"model": "string"`. Use `"gpt-4o-mini"` or omit `model`.

---

## Next

Week 2 RAG → `docs/week2-official-lab.md` · say **Coach me through Week 2**
