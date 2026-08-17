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

Agent stubs (GitHub): [CTATX/my-project/.claude/agents/](https://github.com/CTATX/my-project/tree/main/.claude/agents/)

Bootcamp agent: [.claude/agents/ai-eng-bootcamp-agent.md](.claude/agents/ai-eng-bootcamp-agent.md) · also in [my-project](https://github.com/CTATX/my-project/blob/main/.claude/agents/ai-eng-bootcamp-agent.md)

Project index entry: [my-project/projects/ai-eng-bootcamp](https://github.com/CTATX/my-project/tree/main/projects/ai-eng-bootcamp)

**TeamOS v2.0 (full — rare):** [my-project/teamOS/v2](https://github.com/CTATX/my-project/tree/main/teamOS/v2)

**Engineering TeamOS:** [ai-build-crew/TEAM_OS.md](https://github.com/CTATX/ai-build-crew/blob/main/TEAM_OS.md)

## Product OS index

| Asset | GitHub |
|-------|--------|
| my-project (home hub) | [CTATX/my-project](https://github.com/CTATX/my-project) |
| badlabz (Product OS assets) | [CTATX/badlabz](https://github.com/CTATX/badlabz) |
| ai-build-crew | [CTATX/ai-build-crew](https://github.com/CTATX/ai-build-crew) |

## Build status

| Piece | Status |
|-------|--------|
| `GET /health`, `POST /ask`, `POST /estimate` | Done |
| Streamlit → API (both pages) | Done |
| Cloud Agent dev environment (`.cursor/environment.json`) | Done — validated end-to-end, merged (#3) |
| Docker + deploy | Next (syllabus) |

Use sidebar: **Cost Estimator** | **Bootcamp Q&A**

### Every session — one command (recommended)

```bash
./start.sh
```

Starts API + Streamlit. **Ctrl+C** stops both. See playbook §4.
