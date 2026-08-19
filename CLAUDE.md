# AI Eng Bootcamp — CT

TAI Labs bootcamp workspace. **Playbook (load on demand):** `docs/ai-eng-bootcamp-playbook.md`

**Invoke:** `Use TeamOS Bootcamp for [topic]` → loads playbook + `.claude/agents/ai-eng-bootcamp-agent.md`

## Default mode

**FACT → CONTROL POINT → ACTION** — concise. Expand on: **Grok**, **Deep dive**, **Harden this**, **Full context**.

## Token rule

Do **not** preload full TeamOS v2.0 or this playbook every session. Load playbook sections when CT invokes Bootcamp agent or asks run/debug/architecture questions in this repo.

## TeamOS index

| Agent | Invoke |
|-------|--------|
| **Bootcamp** | `Use TeamOS Bootcamp for [topic]` |
| COS | `Use TeamOS COS for [topic]` |
| Product | `Use TeamOS Product for [topic]` |
| People Leadership | `Use TeamOS People Leadership for [topic]` |
| Executive Comms | `Use TeamOS Executive for [topic]` |
| Investigation | `Use TeamOS Investigation for [topic]` |
| Documentation Evaluation | `Use TeamOS Documentation Evaluation for [topic]` |

Agent stubs: [BadLabz/Projects](https://github.com/BadLabz/Projects) hub · local [.claude/agents/](.claude/agents/)

Bootcamp agent: [.claude/agents/ai-eng-bootcamp-agent.md](.claude/agents/ai-eng-bootcamp-agent.md)

Project index: [BadLabz/Projects](https://github.com/BadLabz/Projects) — `projects/autozyte`, `projects/spoiler-saver`, `projects/ai-eng-bootcamp`

**Engineering TeamOS:** [ai-build-crew/TEAM_OS.md](https://github.com/CTATX/ai-build-crew/blob/main/TEAM_OS.md)

## Product OS index

| Asset | GitHub |
|-------|--------|
| **BadLabz Projects** (product hub) | [BadLabz/Projects](https://github.com/BadLabz/Projects) |
| AutoZyte (shop platform) | [BadLabz/autozyte](https://github.com/BadLabz/autozyte) |
| Spoiler Saver | Indexed in BadLabz/Projects |
| ai-eng-bootcamp (TAI Labs / training) | [CTATX/ai-eng-bootcamp](https://github.com/CTATX/ai-eng-bootcamp) |
| ai-build-crew | [CTATX/ai-build-crew](https://github.com/CTATX/ai-build-crew) |
| badlabz legacy Product OS assets | [CTATX/badlabz](https://github.com/CTATX/badlabz) |

## Build status

| Piece | Status |
|-------|--------|
| `GET /health`, `POST /ask`, `POST /estimate` | Done (course demo) |
| Streamlit → API (Cost Estimator demo + Q&A) | Done |
| **Cost Estimator product** | **[CTATX/ai-build-crew](https://github.com/CTATX/ai-build-crew)** — not this repo |
| **AutoZyte** (shop, FerdAI, ZyteShelf, Zyren) | [BadLabz/autozyte](https://github.com/BadLabz/autozyte) |
| Docker + deploy (bootcamp API) | Next (syllabus) |

Use sidebar: **Cost Estimator** (demo) | **Bootcamp Q&A**

Cost Estimator home: [`docs/cost-estimator-home.md`](docs/cost-estimator-home.md) · local `~/ai-build-crew`  
AutoZyte: `~/autozyte` or nested `autozyte/` · [`docs/autozyte-split.md`](docs/autozyte-split.md)

Playbook: `docs/ai-eng-bootcamp-playbook.md`
