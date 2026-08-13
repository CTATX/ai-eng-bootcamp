---
name: ai-eng-bootcamp-agent
description: >-
  AI engineering bootcamp runbook — client/server architecture, FastAPI + Streamlit,
  terminals, troubleshooting, and build steps for ai-eng-bootcamp. Use when CT says
  "Use TeamOS Bootcamp for [topic]" or when working in ai-eng-bootcamp and needs
  run/restart/debug guidance without re-explaining fundamentals.
---

# AI Eng Bootcamp Agent

**Authoritative playbook:** `docs/ai-eng-bootcamp-playbook.md` — load that file for full TOC, runbooks, and troubleshooting.

## When to use

- Starting or restarting server/client
- Connection refused, port in use, `.env` / API key issues
- Explaining client vs server vs contract
- Build steps A–E and how they map to ai-build-crew

## Default response

FACT → CONTROL POINT → ACTION. Point to the playbook section. Do not re-teach from scratch if the playbook covers it.

## Invoke pattern

`Use TeamOS Bootcamp for [topic]`

Examples:
- `Use TeamOS Bootcamp for restart server`
- `Use TeamOS Bootcamp for connection refused`
- `Use TeamOS Bootcamp for grok architecture`

## Related

- Repo: `/Users/ctansted/ai-eng-bootcamp`
- Product reference: [CTATX/ai-build-crew](https://github.com/CTATX/ai-build-crew)
- Syllabus: [Software components for beginners](https://tailabs.ai/ai-eng-syllabus/pre-course/software-components-for-beginners/)
