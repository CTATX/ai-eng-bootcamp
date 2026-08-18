# Shop intelligence — JTBD and requirements (running)

**Status:** rough cut, living. Append when CT shares more. Do not polish away intent.  
**Owner:** CT (shop owner / product).  
**Last updated:** 2026-08-18

Related: [plan](shop-intelligence-plan.md) · [briefing schema](shop-intelligence-briefing.schema.json)

This file is the **intake log**. The plan is the **build order**. If they disagree, this file wins on *what is wanted*; the plan wins on *when and how we stay legal and cheap*.

---

## Jobs to be done

| ID | Job | Who | Outcome |
|----|-----|-----|---------|
| J1 | Know what a car usually needs in *this* shop | Owner / advisor | Identity + common reasons + parts + ticket range from **our** history |
| J2 | Brief the advisor in one pass | Advisor | Crisp outlined card, not a chat novel |
| J3 | See uncertainty | Advisor | % only with `n`; best/worst from observed jobs; gaps called out |
| J4 | Quote without guessing | Advisor + quote agent (later) | Lines from sold history; human accepts before customer sees it |
| J5 | Source parts | Parts / advisor | Compare vendors on distance, cost, quality, availability |
| J6 | Run the job like a counted procedure | Tech + advisor | Checklist: inspect → do → return unused → count tools → close |
| J7 | Close the money and the shelf | Advisor / accounting | Bundle, restock reco, payment closeout |
| J8 | Attach how-to to the job | Tech | Schematics, take-apart, build steps, images, videos per job (later) |
| J9 | Prototype without production keys or token burn | CT | Synthetic warehouse + screens now; ShopMonkey key later |
| J10 | Advisor gets a hypothesis before talking to the customer | Jake (service advisor persona) | One-pass briefing: vehicle match, top reasons, parts, ticket/time, gotchas — FACT / INFERRED / UNKNOWN |

---

## Persona — Jake (service advisor)

**Who:** Jake is the **human service advisor persona** we design for — not customer-facing chat, not a ShopMonkey reskin, **not an AI agent name**.

**Naming rule (locked):**  
- **Jake** = role + UX voice (“briefing for the advisor at the desk”).  
- **FerdAI** = anything that reasons, orchestrates, or runs as an agent (hypothesis engine, chat, quote agent).  
- Code/APIs use `advisor` (e.g. `POST /advisor/hypothesis`), not `jake` as a system id.

See [autozyte-product-hierarchy.md](autozyte-product-hierarchy.md) for full product map.

**Job:** When a car comes in (VIN or YMM + complaint), produce a **data-based hypothesis** from **this shop's** stored history before Jake (the human) quotes ETA or scope to the customer.

**Output shape:** Crisp outlined card (briefing JSON + Streamlit page), not a chat novel.

**Guardrails (locked):**
- Every claim tagged **FACT** (in warehouse), **INFERRED** (small-n aggregation), or **UNKNOWN** (gap called out).
- **No silent fill.** Orchestrator slots (staff, vendors, procedure, tools) stay UNKNOWN until built.
- **Human gate:** Jake approves before the customer hears ETA or scope.

**What Jake gets now (P2):**
- Vehicle match (VIN best, else YMM + engine)
- Ranked common reasons from order services
- Parts sold for the top reason
- Observed ticket range and labor hours (when recorded)
- Gotchas from shop history (comebacks, deferred/recommended lines)
- Likelihood statement with explicit `n` — not a Porsche diagnosis

**What Jake does not get yet:** live vendor stock, OEM procedures, torque, 3D, quote agent, checklist agent — see orchestrator UNKNOWN slots.

---

## How to run (Jake cut)

No ShopMonkey key required for synthetic Porsche.

```bash
./start.sh
# Sidebar → Jake Advisor
# Or CLI:
python -m server.shop_cli status
python -m server.shop_cli hypothesis --vin SYNWP020140002 --complaint "AOS"
```

**With ShopMonkey key** (live ingest, P1b):

1. Copy `.env.example` → `.env`
2. Add `SHOPMONKEY_API_KEY` from ShopMonkey → Settings → Integration → API Keys
3. Ingest: `python -m server.shop_cli ingest --max-pages 5` (paginated; resumes watermark)
4. Hypothesis runs on **mixed** warehouse (`source=synthetic|shopmonkey` per row)

API: `POST /advisor/hypothesis` · ingest status `GET /shop/ingest/status`

---

## As shared (rough cut)

### 2026-08-14 — ShopMonkey legal and API

- Look up ShopMonkey APIs: what they allow and what they do not.
- Specific question: can I **reskin** for my work?
- **Answer locked:** no reskin / frame / white-label of ShopMonkey. Official REST v3 integration of **your** licensed shop data is allowed.

### 2026-08-14 — “cool go”

- Proceed on the **integration** path, not a reskin.

### 2026-08-14 — Shop-owner product (expensive → plan first)

- Licensed ShopMonkey customer. Stay inside legal bounds.
- Fetch and **store** history over the last few years.
- From that history, identify:
  - the car
  - most common reason it comes in
  - parts list for that reason
  - average ticket cost
  - gotchas that were identified
- Automotive **clean colors and structure**.
- **Input = chat window.** Output = crisp, specific, outlined structure (not a wall of prose).
- Self-feedback: **% likelihood** + recommendations.
- **Guardrail:** no conclusion made to fill in or assume. If it is not fact-based, identify it.
- Callout shape: “X% likely… best and worst case… parts needed… expected time.”
- Later: **multi-agent**
  - create a quote
  - find best parts and alternatives (distance, cost, quality, availability, …)
  - give the service advisor what to do / what to look for
  - checklist similar to a doctor/operation count: what gets done, how to close, tools accounted for
  - unused parts returned to shop inventory
  - recommended bundle, recreate, recommended restock
  - accounting / payment closeout
- Because this is expensive: **plan and structure first**.

### 2026-08-14 — P1 without a key (this cut)

- Prototype P1 **without** the ShopMonkey key. Intent is there; do not block on credentials.
- **Synthetic data** to stand the warehouse and screens up.
- Limit to **Porsche, model years 1980–2025**.
- Limit instance count to a **valid prototype size** (enough for trend visuals, not a fake enterprise dump).
- Artifacts / screens:
  - trend visuals
  - product list
- Product list sourced in the UI as places like **Pelican Parts**, **WorldPac**, etc.
  - Those are mostly open storefronts we can **populate a prototype list** against as **named sources**.
  - **Do not scrape** those sites. **Do not copy** catalogs, images, or copyrighted manuals.
  - Prototype rows are **synthetic SKUs/prices**, labeled as such.
- Eventually each job should carry:
  - designs
  - schematics
  - take-apart steps
  - build steps
  - images
  - videos
- Need a **running doc in git** of JTBD and requirements as they are shared (this file). Rough cut is fine.

---

## Constraints (locked unless CT changes them)

| Kind | Rule |
|------|------|
| Legal | Official ShopMonkey API when a key exists. No reskin, scrape, or clone of ShopMonkey. |
| Legal | No scraping Pelican, WorldPac, or other vendor sites. Named vendors in a prototype list is OK. Live inventory APIs only with a real agreement later. |
| Legal | No OEM/copyrighted schematics, videos, or take-apart manuals in the repo. Slots exist; content is UNKNOWN until we have rights. |
| Truth | FACT / INFERRED / UNKNOWN. No silent fill. |
| Cost | No model tokens in P1–P2. Chat (P3) and agents (P4+) wait. |
| Scope now | Synthetic Porsche 1980–2025 warehouse + trend and parts screens. |
| Audience | Shop owner / service advisor. Not customer-facing chat. |

---

## Prototype data bounds (P1 synthetic)

| Thing | Bound | Why |
|-------|-------|-----|
| Make | Porsche only | CT cut |
| Model year | 1980–2025 inclusive | CT cut |
| Vehicles | 72 | Enough mix, still countable |
| Orders | ~420 across 2016–2025 shop years | Trend lines without a warehouse dump |
| Parts catalog | ~40 synthetic SKUs | Product-list screen |
| Vendors (labels only) | Pelican Parts, WorldPac, Porsche Classic, Suncoast, Shop stock | Named sources, fake SKUs |
| Job media | Slots per job family, empty except a shop-authored checklist stub | Shows the hole honestly |

Source tag on every warehouse row: `synthetic`. Screens must say so.

---

## Screens (this cut)

1. **Status** — synthetic, no ShopMonkey key, row counts.
2. **Trends** — ticket by year, reason mix, model mix, comebacks.
3. **Product list** — catalog by vendor (synthetic).
4. **Job packet holes** — designs / schematics / steps / media = UNKNOWN until licensed content exists.
5. **Jake Advisor** — intake → hypothesis briefing (P2). No LLM.

Chat orchestrator and specialist agents are **specified**, not built.

---

## Open questions

- Which real parts API (if any) after synthetic: WorldPac partner, dealer, other?
- Comeback window days (default 30).
- Where licensed procedures/media will come from (shop-shot video vs licensed publisher).
- When the ShopMonkey key is available, ingest **replaces** synthetic or sits beside it (`source=synthetic|shopmonkey`).

---

## Changelog

| Date | Change |
|------|--------|
| 2026-08-14 | Created from CT messages (legal, product vision, plan-first, synthetic P1, running doc). |
| 2026-08-18 | Locked product hierarchy: AutoZyte, FerdAI, ZyteShelf family, Jake persona — [autozyte-product-hierarchy.md](autozyte-product-hierarchy.md). |
| 2026-08-18 | Jake persona (J10), P2 hypothesis CLI + API + Streamlit page; P1b ingest mapper. |
| 2026-08-14 | Posted actual GitHub paths + screenshots for all three app experiences: [docs/experiences.md](experiences.md). |
