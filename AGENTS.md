# AGENTS.md

## Cursor Cloud specific instructions

This repo is a small two-process app (see `README.md` and `docs/ai-eng-bootcamp-playbook.md` for full details):

- FastAPI server — `server.main:app` on port 8000 (`GET /health`, `POST /estimate`, `POST /ask`)
- Streamlit client — multi-page UI on port 8501 (`app.py` home, `pages/1_Cost_Estimator.py` → `/estimate`, `pages/2_Bootcamp_QA.py` → `/ask`)

### Environment
- Python 3.12. The startup update script creates `.venv/` and installs `requirements.txt` (a superset of `requirements-api.txt`, which is Docker/prod-only). Use the interpreters at `.venv/bin/*`.
- System package `python3.12-venv` is required to create the venv and is already present in the environment build.

### Running the services
- Both processes must run at once. Start each in its own long-lived shell (e.g. tmux), not the same command.
- API: `.venv/bin/uvicorn server.main:app --reload --host 127.0.0.1 --port 8000`
- Client: `.venv/bin/streamlit run app.py --server.headless true --server.port 8501 --server.address 0.0.0.0`
  - `--server.headless true` is important in a headless VM: it skips Streamlit's first-run interactive email prompt, which would otherwise block startup.
- `start.sh` also boots both (API in background + Streamlit foreground) but expects an activated `.venv`; the two explicit commands above are more reliable for agents.

### Gotchas
- The Streamlit client reaches the API via `API_BASE` (default `http://127.0.0.1:8000`, see `api_client.py`). If the "Connected to your API" banner is missing, the uvicorn process isn't running.
- `POST /ask` (Bootcamp Q&A page) requires a real `OPENAI_API_KEY` (in `.env` or the environment). Without it the endpoint returns a 503/401. `GET /health` and `POST /estimate` (Cost Estimator page) need no key and are the reliable path to exercise the app end-to-end.
- No test suite or lint config exists in this repo; there is nothing to run for automated tests/lint.
