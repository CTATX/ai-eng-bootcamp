# Prompt complexity and cost forecasting

This bootcamp app forecasts **how much work a prompt will take** and what it will **cost in USD** — before you run it.

## Two cost bands

| Band | What it means | Formula |
|------|---------------|---------|
| **Broad range (x → y)** | Full envelope across the 5-model catalog | Min cost (cheapest model, **low** scenario) → max cost (priciest model, **high** scenario) |
| **Closer delta (±δ)** | Tighter band around the likely recommendation | **Likely** cost for the recommended model ± **uncertainty** driven by prompt complexity |

**Example:** Broad `$0.0012 – $0.0089` per task; closer `$0.0031 ± $0.0005` per task on Gemini 2.5 Flash.

Uncertainty widens when the prompt is ambiguous or agentic (more retries, harder to predict).

## Complexity dimensions (1–5 each)

| Dimension | What we detect | Drives |
|-----------|----------------|--------|
| Input size | Token count (+ buffer) | `input_tokens` |
| Output depth | report, paragraph, one-line | `result_shape` |
| Reasoning depth | compare, plan, debug | `primary_steps` |
| Verification need | double-check, compliance | `checker_steps` |
| Ambiguity risk | vague scope, “best effort” | **uncertainty %** (close delta width) |
| Agentic pattern | tools, loops, multi-step | `primary_steps` |

Composite score → label: **Simple / Moderate / Complex / Agentic**.

## API

```bash
curl -X POST http://127.0.0.1:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"prompt_text": "Summarize this 10-page contract and flag warranty risks.", "tasks_per_day": 50}'
```

Response includes `complexity`, `workload_derived`, `cost_ranges`, `rationale`, and full `estimate`.

## Netflix Headroom — what it is (and what it is not)

**Headroom is not a “network engine” in the CDN sense.** Netflix uses the word *headroom* in two different places:

1. **Headroom (LLM tool)** — open-source library by Netflix engineer Tejas Chopra: [github.com/chopratejas/headroom](https://github.com/chopratejas/headroom). Middleware that **shrinks context before it hits the model** (compression, cache alignment, tiered routing). Reported savings: **50–90% fewer tokens** on agent workloads with reversible compression (CCR: compress → model can retrieve originals via MCP).

2. **Fleet “headroom” (capacity planning)** — classic ops term: **buffer between offered load and failure** (e.g. handle 4× traffic before congestive collapse). That’s about **servers and traffic**, not LLM tokens.

For **this cost estimator**, we borrow Headroom’s *idea*: redundant prompt/context tokens can be trimmed, which **narrows your cost range toward the lower bound**.

Toggle `apply_headroom: true` on `/analyze` to forecast with an estimated input-token reduction (15–55% depending on prompt size and agent patterns).

### Headroom techniques (teaching map)

| Headroom concept | Problem it solves | Cost estimator analog |
|------------------|-------------------|------------------------|
| **CacheAligner** | Resend only changed context | Lower `input_tokens` on repeat tasks |
| **Compression routers** | JSON/logs/code bloat | Smaller effective input → lower broad range floor |
| **CCR (reversible compression)** | Cheap default, retrieve if needed | Fewer tokens per call; occasional retrieve adds a small step |
| **Tiered model routing** | Wrong model for subtask | Our catalog comparison + `recommend_model()` |

### How Headroom relates to broad vs close delta

- **Broad range** = “worst reasonable case” (big context, expensive model, high retries).
- **Headroom** pulls the **left side** of that range down by cutting waste tokens.
- **Close delta** = “best single-model guess” ± ambiguity; Headroom makes the center move **down** without changing the formula.

## Limits (be honest)

- Heuristic analyzer is the default (no API spend). Optional LLM classifier uses `gpt-4o-mini` (~$0.0001–0.002/prompt).
- Cannot predict unknown RAG chunks or tool loops not described in the prompt.
- Dollar amounts use the bootcamp **`models.json`** catalog (illustrative prices), not live provider billing.

## Optional LLM classifier (Phase 2)

Set `use_llm_classifier: true` on `/analyze` (or toggle in Streamlit sidebar). Requires `OPENAI_API_KEY` in `.env`.

- Caps input at 4,000 characters
- Returns structured JSON dimensions + step hints
- Merges with heuristics: LLM used when confidence ≥ 0.5; pure LLM when ≥ 0.85
- Session-level cache avoids repeat charges for identical prompts

## Per-model complexity adjustment

Frontier models in `models.json` (Sonnet, Terra) include `complexity_step_adjustment`: when `reasoning_depth ≥ 4`, primary steps drop by 1 (min 1). This reflects cheaper total cost on hard reasoning when using a stronger model.

## Files

- `prompt_analyzer.py` — complexity scoring + workload mapping + LLM merge
- `cost_engine.py` — `forecast_cost_ranges()` broad + close math + step adjustment
- `server/analyze_service.py` — `POST /analyze` orchestration
- `server/openai_client.py` — optional `classify_prompt_complexity()`
