# AutoZyte product hierarchy (locked)

**Status:** locked naming — 2026-08-18  
**Owner:** CT  
**Purpose:** Clean separation for repos, agents, and customer-facing brands. Load this before splitting code out of `ai-eng-bootcamp`.

---

## Parent and brands

| Name | Type | Customer-facing? | Role |
|------|------|------------------|------|
| **AutoZyte** | Product (parent) | **Yes** | Licensed shop operations platform — your UI, warehouse, workflows. Not ShopMonkey. |
| **FerdAI** | AI / processing layer | **Badge only** (“Intel Inside”) | Hypothesis, orchestration, agents, guardrails. Powers AutoZyte; not the shop brand. |
| **Zyren** | AR companion | **Yes** (when shipped) | Augmented reality layer in bay — consumes Shop + ZyteShelf + FerdAI context. |
| **ShopMonkey** | Vendor / SMS | **No** | Official API ingest only. Never product name. |
| **Jake** | **Persona** (human role) | **No** | Service advisor we design **for** — not an AI agent name. |
| **AI Eng Bootcamp** | Teaching repo | N/A | Separate from production. No AutoZyte code long-term. |

### FerdAI “Intel Inside”

- **Customer sees:** AutoZyte (and Zyren when live).
- **Optional badge:** “Powered by FerdAI” on advisor surfaces, settings, or footer — not on customer RO copy unless intentional.
- **FerdAI owns:** model calls, agent routing, FACT / INFERRED / UNKNOWN enforcement, orchestrator.
- **AutoZyte owns:** shop data, UI, ingest, inventory, legal boundary with ShopMonkey.

---

## Jake — persona, not agent

**Interpretation (locked):**

| Jake is | Jake is not |
|---------|-------------|
| The **service advisor persona** — the human at the desk | An AI agent name |
| The **UX voice** (“briefing for the advisor”) | A model, bot, or autonomous worker |
| The **approval gate** before customer hears ETA/scope | Customer-facing chat brand |
| A simple, memorable **role label** in docs and UI copy | A replacement for FerdAI in architecture |

**Technical naming (use in code / APIs / repos):**

| Layer | Name | Example |
|-------|------|---------|
| Persona (UI copy) | Jake | “Jake Advisor” page, “Briefing for Jake” |
| Capability (FerdAI) | Advisor hypothesis, advisor briefing | `POST /advisor/hypothesis`, `AdvisorHypothesis` |
| Engine (no LLM today) | Hypothesis engine | `shop_hypothesis.py` → moves to `ferdai/` or `shop/` |
| Future LLM agent | FerdAI Advisor (or named sub-agent) | e.g. `ferdai.advisor.chat` — **not** “Jake AI” |

**Rule:** If it **reasons, calls tools, or runs autonomously** → **FerdAI** module + agent id.  
If it **describes who consumes the output** → **Jake** persona in product copy only.

---

## Repo / folder tree (target)

```text
CTATX/autozyte/
├── shop/              # History warehouse, ShopMonkey ingest, advisor UI surfaces
├── ferdai/            # AI layer — hypothesis, orchestrator, agents (supports AutoZyte)
├── zyteshelf/         # Inventory parent (see ZyteShelf family below)
├── zyren/             # AR companion holding — pulls Shop + ZyteShelf + FerdAI
└── docs/
    └── autozyte-product-hierarchy.md   # this file
```

---

## ZyteShelf family (locked)

**Parent module: ZyteShelf** — inventory management for the shop floor and back room.

Sub-modules reduce agent scope — each owns one slice of shelf work:

| Module | Scope | Owns | Does not own |
|--------|-------|------|--------------|
| **ZyteShelf** | Inventory parent | Module charter, shared models, “shelf in / shelf out” JTBD | Shop history analytics, SMS ingest |
| **ZyteBin** | Physical placement | Bin location, aisle/shelf slot, pick path | Vendor catalogs, ticket pricing |
| **ZyteStock** | Quantity state | On-hand, reserved, allocated, low-stock signals | Shop order history (that’s `shop/`) |
| **ZyteLedger** | Closeout & restock | Returns, restock reco, job-to-shelf reconciliation, accounting tie-out | Live WorldPac/Pelican APIs (future P5) |

**Agent workload rule:** When a task mentions **where on the shelf** → ZyteBin. **How many** → ZyteStock. **Return/restock/close ticket** → ZyteLedger. **General inventory** → ZyteShelf.

---

## Data boundaries (agents)

| System | Data | Source |
|--------|------|--------|
| **shop/** | Order history, vehicles, Jake briefing inputs | ShopMonkey ingest + shop warehouse |
| **ZyteShelf** | Current shelf truth | Shop stock, returns, counts, future integrations |
| **FerdAI** | Reasoning over shop + shelf JSON | Never calls ShopMonkey live for history |
| **Zyren** | Presentation of fused context | Read-only from shop + ZyteShelf + FerdAI |

---

## Phases vs products

| Phase | Product home |
|-------|----------------|
| P1–P2 warehouse, Jake briefing, ingest | `autozyte/shop/` + `ferdai/` hypothesis |
| P3 guardrailed chat | `ferdai/` |
| P4–P7 agents (quote, parts, checklist) | `ferdai/agents/` |
| Inventory / returns / restock | `zyteshelf/` (+ Bin, Stock, Ledger) |
| AR companion | `zyren/` |

---

## Changelog

| Date | Change |
|------|--------|
| 2026-08-18 | Locked AutoZyte parent, FerdAI Intel Inside, Jake persona vs agent, ZyteShelf family. |
