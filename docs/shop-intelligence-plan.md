# Shop intelligence — plan (P0)

**Status:** P0 plan locked. P1 synthetic warehouse and screens in this repo. No live ShopMonkey ingest. No OpenAI spend.  
**Mode:** licensed shop owner → official ShopMonkey REST v3 → **our** warehouse and **our** UI.  
**Not this product:** reskin, iframe, or white-label of ShopMonkey.

Sources: [shopmonkey.dev](https://shopmonkey.dev/overview) · [Terms](https://www.shopmonkey.io/legal/terms-of-service) · [Acceptable use](https://www.shopmonkey.io/legal/acceptable-use-policy)

---

## 1. Decision (locked)

| Rule | Meaning |
|------|---------|
| Legal path | Internal business use of **your** shop data through the **official API**. Allowed under a paid ShopMonkey license. |
| Illegal / blocked path | Copy, frame, or restyle ShopMonkey; scrape the app; clone their UI; resell their product. |
| Cost path | Warehouse first. Chat second. Multi-agent last. Do not pay model tokens until facts are queryable locally. |
| Truth path | Every number on screen is **FACT**, **INFERRED**, or **UNKNOWN**. Nothing is filled in to look complete. |

You own Customer Data in ShopMonkey (ToS). Storing a copy in our warehouse for your shop’s analysis is the integration they document. Building **your** advisor briefing is allowed. Building a ShopMonkey lookalike is not.

---

## 2. What you asked for → when it ships

| You want | Phase | Spend |
|----------|-------|--------|
| Fetch years of shop history and store it | **P1** Ingest | Synthetic now (no key). ShopMonkey API when the key exists. |
| Identify the car; common reasons; parts; average ticket; gotchas | **P2** Fact model | $0 model tokens |
| Automotive-clean UI + chat that returns a crisp outlined briefing | **P3** Guardrailed chat | Cheap model, warehouse-only context |
| % likelihood, best/worst case, parts, expected time | **P3** (only if sample exists) | Same |
| Quote agent; parts alternatives (distance, cost, quality, availability) | **P4–P5** | Expensive; human-in-loop |
| Advisor checklist (operate → close → count tools → return unused parts) | **P6** | Expensive |
| Bundle / restock / payment closeout | **P7** | Expensive |

**Do not start P4+ until P2 can answer a real vehicle with `n` orders and an explicit UNKNOWN list.**

---

## 3. Target architecture

```text
Synthetic Porsche seed (P1, no key)
        │
        ▼
┌─────────────────────────────────────────┐
│  Warehouse (SQLite)                     │
│  vehicles, orders, line items,          │
│  catalog, artifact slots                │
└─────────────────────────────────────────┘
        │
        ▼
  Trend + product-list screens (this cut)
        │
        ▼
ShopMonkey REST ingest (P1b, when key exists)
        │
        ▼
  Fact layer → briefing chat → agents (P2–P7)
```

Streamlit (or later a dedicated UI) talks to **our** FastAPI. Only the server talks to ShopMonkey. Chat never calls ShopMonkey live for history.

---

## 4. Fetch and store (P1)

### 4.1 What we pull

| Warehouse table | ShopMonkey source | Why |
|-----------------|-------------------|-----|
| `vehicles` | `/v3/vehicle` | Identify the car (VIN, YMM, plate, engine) |
| `orders` | `/v3/order` | Ticket, dates, status, customer, vehicle |
| `order_services` | `/v3/order/:id/service` | “Why it came in” (service names + notes) |
| `order_parts` | order part lines | Parts list + cost |
| `order_labor` | order labor lines | Time and labor $ |
| `order_tires` / `order_fees` | tire and fee lines | Complete ticket |
| `inspections` + `inspection_items` | `/v3/inspection` | Recommended work = gotcha candidates |
| `deferred_services` | customer/vehicle deferred | Comeback / “we already saw this” |
| `payments` | `/v3/integration/payment` | Closeout $ (later P7) |
| `ingest_watermark` | local | Resume years of backfill |

Auth: Bearer key from **Settings → Integration → API Keys**. Key inherits the admin who created it. Store in `.env` as `SHOPMONKEY_API_KEY`. Never commit.

### 4.2 Years of history

REST v3 is paginated (`limit` / `skip` / `where`). There is no public sandbox. Enterprise Data Streaming is a separate paid firehose — **not required for prototype**.

P1 backfill rules:

1. Walk orders oldest → newest (or newest → oldest) with a stored watermark.
2. Honor `429` + `Retry-After`. Sleep. Do not hammer.
3. One shop, one location first. Multi-shop later.
4. Idempotent upserts on ShopMonkey `id`.
5. Stop if a page fails; resume from watermark. Do not silently skip years.

### 4.3 What the API will not give us

| Desired field | Reality |
|---------------|---------|
| “Gotcha” as a first-class object | Does not exist. We **define** gotchas from inspections, deferred services, notes, and repeat visits. Label must say so. |
| True clock time on every job | Labor hours exist when techs clocked or entered time. Missing time = **UNKNOWN**, not a guess. |
| Parts vendor distance / quality / stock at AutoZone | Not in ShopMonkey. P5 needs a **different** parts API. Do not fake it. |
| Why the customer *thought* they came in | Only if a complaint/note was typed. Otherwise UNKNOWN. |

---

## 5. Fact model (P2) — the questions you listed

All of these are **aggregations on stored orders**. No model in the loop.

| Question | Fact method | Guardrail |
|----------|-------------|-----------|
| Identify the car | Exact VIN, else YMM + engine/submodel | If VIN missing, say match is YMM-only |
| Most common reason | Count of service names (and inspection “recommended” items) for that vehicle identity | Do not rename “Brake job” to “safety failure” |
| Parts list for that | Distinct parts on orders with that reason | Show frequency and last-seen date |
| Average ticket | Mean / median / p25 / p75 of invoiced $ | Show `n`. If `n < 5`, suppress “average” as a recommendation and show the raw list |
| Gotchas | (a) inspection items flagged recommended and not sold, (b) deferred services, (c) same vehicle back within N days | Each row cites order id + date. No narrative gotcha without a row |

**Comeback window (default):** 30 days. Configurable. Not a medical diagnosis — a repeat-visit count.

**Vehicle identity grain (default):** VIN if present, else `year+make+model+engine`. Mixing grains in one briefing is forbidden.

---

## 6. Guardrails (non-negotiable)

Every claim on a briefing card carries one tag:

| Tag | Meaning | UI |
|-----|---------|----|
| **FACT** | Counted from warehouse rows | Body text, tables |
| **INFERRED** | Statistical from those rows (mean, %, cluster) | Callout with `n` and method |
| **UNKNOWN** | Not in the data; we will not fill it | Dedicated “Not in data” rail |

Rules:

1. **No silent fill.** If labor hours are missing on 40% of jobs, expected time is UNKNOWN or a range **only from the jobs that have hours**, with the missing % stated.
2. **No conclusion without `n`.** Likelihood % is `count_with_pattern / count_in_match`. If match set is empty, return UNKNOWN and stop.
3. **Best / worst case** = observed p25 / p75 (or min/max if `n < 10`), not an invented scenario.
4. **Chat may retrieve and format. Chat may not invent parts, times, or diagnoses.**
5. If the model wants to say something not in the retrieved facts, it goes to **UNKNOWN** or is dropped.
6. Human (service advisor) accepts before any quote is sent to a customer (P4+).

Contract file: [`shop-intelligence-briefing.schema.json`](shop-intelligence-briefing.schema.json)

---

## 7. Chat + briefing UI (P3)

**Input:** one chat box. Shop owner / advisor types like: `2018 F-150 5.0, brakes, 92k`.

**Output:** not a paragraph. A **briefing card** that matches the schema:

1. Vehicle match (grain + how many orders)
2. Date range of evidence
3. Common reasons (ranked, with share)
4. Parts list for the selected reason (frequency, last seen)
5. Ticket: typical / best-observed / worst-observed
6. Time: only if labor hours exist
7. Gotchas with source rows
8. Likelihood callout: “Based on **n** jobs, **X%** had this pattern. Best observed ticket $A. Worst observed $B.”
9. **Not in data** rail
10. Recommendations that are only “do / check / ask” derived from facts — never “this is definitely the failure”

### Visual (ours, not ShopMonkey)

Automotive shop floor, not a consumer app and not their product:

| Token | Use |
|-------|-----|
| Graphite `#1B1F24` | Background |
| Paper `#F4F1EA` | Cards |
| Steel `#5C6770` | Secondary text |
| Safety amber `#E8A317` | INFERRED callouts |
| Signal red `#C0392B` | UNKNOWN / missing data |
| Pit-lane green `#2F6B4F` | FACT metrics, complete jobs |
| Type | Sentence case, tight hierarchy, numbers tabular |

No iframe of ShopMonkey. No copying their layout or graphics.

---

## 8. Multi-agent (P4–P7) — designed, not built

Each agent has a **written contract** and a **human gate**. None run until P2 `n` and guardrails exist.

| Agent | Job | Inputs (facts) | Must not |
|-------|-----|----------------|----------|
| **Quote** | Draft estimate lines from briefing parts + labor rates | Warehouse parts, labor rates, shop matrices | Invent a job the shop has never sold without UNKNOWN |
| **Parts scout** | Rank alternatives: cost, availability, distance, quality | **External** parts APIs (not ShopMonkey) | Pretend ShopMonkey has vendor aisle stock |
| **Advisor checklist** | Intra-op list: inspect → do → torque/spec → unused parts back to bin → tools accounted | Service + inspection items | Skip “return unused” or “count tools” |
| **Closeout** | Bundle / restock reco + payment status | Payments, remaining qty, deferred | Close a ticket the advisor has not accepted |

Checklist shape (P6), analogous to a surgical count — **shop language, not medical advice**:

1. Confirm vehicle identity (VIN)
2. Confirm complaint vs last visits
3. Inspect (from inspection template if one exists)
4. Do work (from sold + recommended lines)
5. Unused parts → inventory return
6. Tools / special equipment accounted
7. Road test / quality gate if the shop uses one
8. Advisor review → customer authorization
9. Invoice / payment
10. Restock reco from what was consumed

---

## 9. Cost control

| Phase | Model calls | Why |
|-------|-------------|-----|
| P1–P2 | None | Ingest + SQL |
| P3 | One structured completion per question, warehouse JSON in context | Briefing only |
| P4–P7 | Multiple agents | Blocked until P3 is trusted on real shop data |

Daily budget already exists as a bootcamp pattern (`/ask`). Reuse a hard cap before P3 goes live.

---

## 10. Build order (next session starts at P1)

**P0 — this document.** Locked.

**P1 — warehouse (this cut, no key):** Synthetic Porsche 1980–2025 SQLite warehouse + trend / product-list screens. ShopMonkey client waits for a real key.

**P1b — live ingest:** ShopMonkey client, watermark, backoff. Replaces or sits beside `source=synthetic`.

**P2 — fact API:** `POST /shop/briefing/preview` that returns the schema from SQL only (chat box can wait).

**P3 — chat UI:** fills the same schema; UNKNOWN rail required.

**P4+** only after you have used P2 on real vehicles and said the facts look right.

---

## 11. Out of scope until you say go

- Training a model on shop data
- Customer-facing chat (this is advisor/owner)
- Scraping ShopMonkey UI
- Parts-vendor integrations before a named provider
- Medical/diagnostic claims beyond “what this shop has sold/inspected”
