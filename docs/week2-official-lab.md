# Week 2 — Official lab (RAG + vector databases)

**Cohort source:** [week-2/rag-vector-databases](https://github.com/akshika47/AI-Internship/tree/main/ai-engineering-bootcamp-v2/week-2/rag-vector-databases)

**Finish line:** Notebook Parts 1–7 run in order; Part 6 Document Q&A returns a grounded answer.

**Notebook:** `rag_vector_databases_live_session.ipynb`

---

## Setup (once)

```bash
cd ~/AI-Internship/ai-engineering-bootcamp-v2/week-2/rag-vector-databases
cp .env.example .env
# same OPENAI_API_KEY as week-1 — never paste in chat
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Stop Week 1 servers** if still on port 8000 — not required for notebook, but avoids confusion.

---

## Run the notebook

**Option A — Jupyter in browser:**

```bash
cd ~/AI-Internship/ai-engineering-bootcamp-v2/week-2/rag-vector-databases
source .venv/bin/activate
jupyter notebook rag_vector_databases_live_session.ipynb
```

**Option B — Cursor:** open the `.ipynb` in Cursor and run cells top to bottom.

---

## Notebook map (one part = one coach step)

| Part | Topic | You'll know it worked when |
|------|-------|----------------------------|
| 1 | Why RAG exists | You can name the LLM limitation RAG fixes |
| 2 | RAG architecture | You can draw index → retrieve → augment → generate |
| 3 | Embeddings | Similarity matrix / vectors print without error |
| 4 | Chunking | Fixed vs recursive vs markdown splits make sense |
| 5 | Vector DB | Chroma similarity search returns relevant chunks |
| 6 | Live Document Q&A | Question about sample doc → grounded answer |
| 7 | Evaluation | RAGAS / debug cells run |

**Rule:** Run cells **in order**. Each part builds on the last.

---

## UAT corner cases (Week 1 lesson applies)

| Symptom | Likely cause |
|---------|----------------|
| `OPENAI_API_KEY` missing | `.env` in **this** folder, restart kernel |
| Chroma duplicate errors | Re-run Part 5 cell (notebook resets collection) |
| Empty retrieval | Chunk size too small — Part 4 demo shows this |
| Kernel wrong Python | Select `.venv` kernel in Jupyter |

---

## Cost note

Embeddings + LLM calls in the notebook spend tokens. Same key as Week 1 — watch usage if needed.

---

## Tie to `ai-eng-bootcamp`

Week 2 lab is **notebook-first** (LangChain + Chroma), not FastAPI stages. Your bootcamp repo `/ask` is still the Week 1 client/server stack. Week 2 adds **how to ground answers in documents** — the pattern FerdAI and shop intel will use later.

---

## Coach phrases

`Coach me through Week 2` · `What's next?` · **done** · **stuck**

Progress: **`docs/week2-progress.md`**
