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

Agent stubs (GitHub): [GTInternational/Projects](https://github.com/GTInternational/Projects) hub · local [.claude/agents/](.claude/agents/)

Bootcamp agent: [.claude/agents/ai-eng-bootcamp-agent.md](.claude/agents/ai-eng-bootcamp-agent.md)

Project index: [GTInternational/Projects](https://github.com/GTInternational/Projects) — see `projects/ai-eng-bootcamp`, `projects/autozyte`, `projects/spoiler-saver`

**Engineering TeamOS:** [ai-build-crew/TEAM_OS.md](https://github.com/CTATX/ai-build-crew/blob/main/TEAM_OS.md)

## Product OS index

| Asset | GitHub |
|-------|--------|
| **GTInternational Projects** (home hub) | [GTInternational/Projects](https://github.com/GTInternational/Projects) |
| AutoZyte (shop platform) | `GTInternational/autozyte` (target repo) |
| Spoiler Saver | Indexed in GTInternational/Projects |
| ai-eng-bootcamp (TAI Labs) | [CTATX/ai-eng-bootcamp](https://github.com/CTATX/ai-eng-bootcamp) |
| ai-build-crew | [CTATX/ai-build-crew](https://github.com/CTATX/ai-build-crew) |
| badlabz (Product OS assets) | [CTATX/badlabz](https://github.com/CTATX/badlabz) |

## Build status

| Piece | Status |
|-------|--------|
| `GET /health`, `POST /ask`, `POST /estimate` | Done |
| Streamlit → API (both pages) | Done |
| Shop intelligence | **P0 plan** + **P1 synthetic Porsche warehouse/screens** |
| Docker + deploy | Next (syllabus) |

Use sidebar: **Cost Estimator** | **Bootcamp Q&A** | **Shop intelligence**

JTBD / requirements (running, rough cut): `docs/shop-intelligence-jtbd.md`  
Published paths + screenshots: `docs/experiences.md`

### Every session — one command (recommended)

```bash
./start.sh
```

Starts API + Streamlit. **Ctrl+C** stops both. See playbook §4.
