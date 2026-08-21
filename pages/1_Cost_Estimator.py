"""AI Cost Estimator — calls POST /estimate and POST /analyze."""

from __future__ import annotations

import requests
import streamlit as st

from api_client import API_BASE, server_is_up

st.title("AI Cost Estimator")
st.caption("Paste a prompt → analyze complexity → see broad cost range and a closer delta.")

if "input_tokens" not in st.session_state:
    st.session_state.input_tokens = 4_000
if "result_shape" not in st.session_state:
    st.session_state.result_shape = "Short answer (≈150 tokens)"
if "primary_steps" not in st.session_state:
    st.session_state.primary_steps = 1
if "checker_steps" not in st.session_state:
    st.session_state.checker_steps = 1
if "pending_analyze_payload" not in st.session_state:
    st.session_state.pending_analyze_payload = None

if server_is_up():
    st.success("Connected to your API")
else:
    st.warning("Your API is not running. Start it in a separate terminal, then refresh.")

with st.sidebar:
    st.header("Assumptions")
    st.markdown(
        "- **Broad range:** cheapest model (low scenario) → priciest (high)\n"
        "- **Close delta:** likely cost ± uncertainty from prompt complexity\n"
        "- **Headroom:** optional context trim (Netflix-style savings)\n"
        "- Monthly = cost/task × tasks/day × 30"
    )
    apply_headroom = st.checkbox("Apply Headroom-style token savings", value=False)
    use_llm_classifier = st.checkbox(
        "Use AI classifier (uses API credits)",
        value=False,
        help="Uses gpt-4o-mini to refine complexity scores when OPENAI_API_KEY is set.",
    )
    with st.expander("Server command (Terminal 1)"):
        st.code("uvicorn server.main:app --reload", language="bash")

result_shapes: list[str] = [
    "Short answer (≈150 tokens)",
    "Paragraph (≈400 tokens)",
    "Report section (≈900 tokens)",
]

col_left, col_right = st.columns(2)

with col_left:
    prompt_text = st.text_area(
        "Paste your prompt",
        placeholder=(
            "Example: Compare three vendor proposals, cite compliance risks, "
            "and produce a one-page executive summary. Double-check all figures."
        ),
        height=160,
    )
    tasks_per_day = st.number_input("Completed tasks per day", min_value=1, max_value=10_000, value=50)

with col_right:
    st.subheader("Workload knobs")
    st.caption("Auto-filled after analyze — adjust manually if needed.")
    input_tokens = st.number_input(
        "Input tokens per task",
        min_value=500,
        max_value=500_000,
        step=500,
        key="input_tokens",
        help="Rough rule: ~750 tokens per page of text.",
    )
    shape_index = result_shapes.index(st.session_state.result_shape) if st.session_state.result_shape in result_shapes else 0
    result_shape = st.selectbox(
        "Expected result size",
        result_shapes,
        index=shape_index,
        key="result_shape",
    )
    primary_steps = st.slider("Primary model steps per task", 1, 5, key="primary_steps")
    checker_steps = st.slider("Checker/review steps per task", 0, 3, key="checker_steps")

analyze_clicked = st.button("Analyze prompt & forecast cost", type="primary", use_container_width=True)
estimate_clicked = st.button("Estimate from manual knobs only", use_container_width=True)


def _render_complexity_table(complexity: dict, analyzer_source: str) -> None:
    st.subheader("Complexity profile")
    st.caption(f"Source: **{analyzer_source}**")
    rows = [
        {"Dimension": "Input size", "Score (1-5)": complexity.get("input_size")},
        {"Dimension": "Output depth", "Score (1-5)": complexity.get("output_depth")},
        {"Dimension": "Reasoning depth", "Score (1-5)": complexity.get("reasoning_depth")},
        {"Dimension": "Verification need", "Score (1-5)": complexity.get("verification_need")},
        {"Dimension": "Ambiguity risk", "Score (1-5)": complexity.get("ambiguity_risk")},
        {"Dimension": "Agentic pattern", "Score (1-5)": complexity.get("agentic_pattern")},
    ]
    st.dataframe(rows, use_container_width=True, hide_index=True)
    chart_data = {row["Dimension"]: row["Score (1-5)"] for row in rows}
    st.bar_chart(chart_data)


def _render_cost_ranges(data: dict) -> None:
    ranges = data.get("cost_ranges")
    if not ranges:
        return

    st.subheader("Cost forecast")
    broad_lo = ranges["broad_min_per_task_usd"]
    broad_hi = ranges["broad_max_per_task_usd"]
    close = ranges["close_center_per_task_usd"]
    close_lo = ranges["close_low_per_task_usd"]
    close_hi = ranges["close_high_per_task_usd"]
    delta = ranges["close_delta_per_task_usd"]
    model_name = ranges.get("recommended_model_name") or "recommended model"

    st.markdown(
        f"**Broad range (all catalog models):** "
        f"${broad_lo:.5f} – ${broad_hi:.5f} per task · "
        f"${ranges['broad_min_monthly_usd']:,.2f} – ${ranges['broad_max_monthly_usd']:,.2f}/month"
    )
    st.markdown(
        f"**Closer delta ({model_name}, likely ± complexity):** "
        f"**${close:.5f}** (±${delta:.5f}) → "
        f"${close_lo:.5f} – ${close_hi:.5f} per task · "
        f"${ranges['close_low_monthly_usd']:,.2f} – ${ranges['close_high_monthly_usd']:,.2f}/month"
    )

    complexity = data.get("complexity", {})
    if complexity:
        st.caption(
            f"Label: **{complexity.get('label', '?')}** · "
            f"score {complexity.get('composite_score', '?')}/30 · "
            f"uncertainty ±{complexity.get('uncertainty_pct', 0):.0%}"
        )


def _render_estimate_block(data: dict, note: str | None = None) -> None:
    recommendation = data.get("recommendation")
    likely_rows = data.get("likely_comparison", [])
    scenario_ranges = data.get("scenario_ranges", [])

    if note:
        st.info(note)

    st.subheader("Recommendation")
    if recommendation is None:
        st.error(
            "No model in the catalog fits this input size. "
            "Reduce input tokens or pick a larger-context model."
        )
    else:
        st.success(
            f"**{recommendation['name']}** ({recommendation['provider']}) — "
            f"${recommendation['cost_per_task_usd']:.5f} per task · "
            f"${recommendation['monthly_usd']:,.2f}/month"
        )

    st.subheader("Likely-scenario comparison")
    if likely_rows:
        st.dataframe(
            [
                {
                    "Model": row["name"],
                    "Provider": row["provider"],
                    "Cost / task (USD)": round(row["cost_per_task_usd"], 6),
                    "Monthly (USD)": round(row["monthly_usd"], 2),
                    "Output tokens": row["output_tokens"],
                    "Attempted calls": round(row["attempted_calls"], 2),
                }
                for row in likely_rows
            ],
            use_container_width=True,
            hide_index=True,
        )

    with st.expander("Low / likely / high for top pick"):
        if scenario_ranges:
            st.dataframe(
                [
                    {
                        "Scenario": row["scenario"],
                        "Cost / task (USD)": round(row["cost_per_task_usd"], 6),
                        "Monthly (USD)": round(row["monthly_usd"], 2),
                    }
                    for row in scenario_ranges
                ],
                use_container_width=True,
                hide_index=True,
            )


if analyze_clicked:
    if not server_is_up():
        st.error("Start the API server first, then try again.")
    elif not prompt_text.strip():
        st.error("Paste a prompt to analyze.")
    else:
        try:
            response = requests.post(
                f"{API_BASE}/analyze",
                json={
                    "prompt_text": prompt_text.strip(),
                    "tasks_per_day": int(tasks_per_day),
                    "apply_headroom": apply_headroom,
                    "use_llm_classifier": use_llm_classifier,
                },
                timeout=60,
            )
            response.raise_for_status()
            payload = response.json()
            derived = payload.get("workload_derived", {})
            if derived:
                st.session_state.input_tokens = derived["input_tokens"]
                st.session_state.result_shape = derived["result_shape"]
                st.session_state.primary_steps = derived["primary_steps"]
                st.session_state.checker_steps = derived["checker_steps"]
            st.session_state.pending_analyze_payload = payload
            st.rerun()

        except requests.ConnectionError:
            st.error("Lost connection to the API. Check that the server is still running.")
        except requests.HTTPError:
            detail = response.json().get("detail", response.text)
            st.error(f"API error ({response.status_code}): {detail}")

elif estimate_clicked:
    if not server_is_up():
        st.error("Start the API server first, then try again.")
    else:
        try:
            response = requests.post(
                f"{API_BASE}/estimate",
                json={
                    "input_tokens": int(st.session_state.input_tokens),
                    "result_shape": st.session_state.result_shape,
                    "primary_steps": int(st.session_state.primary_steps),
                    "checker_steps": int(st.session_state.checker_steps),
                    "tasks_per_day": int(tasks_per_day),
                    "workload_note": prompt_text.strip() or None,
                },
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            _render_estimate_block(data, note="Manual estimate (no prompt analysis).")
        except requests.ConnectionError:
            st.error("Lost connection to the API. Check that the server is still running.")
        except requests.HTTPError:
            detail = response.json().get("detail", response.text)
            st.error(f"API error ({response.status_code}): {detail}")
else:
    if st.session_state.pending_analyze_payload:
        payload = st.session_state.pending_analyze_payload
        complexity = payload.get("complexity", {})
        estimate = payload.get("estimate", {})
        if complexity:
            _render_complexity_table(complexity, payload.get("analyzer_source", "heuristic"))
        _render_cost_ranges(payload)
        if payload.get("rationale"):
            with st.expander("Why this forecast?"):
                for line in payload["rationale"]:
                    st.markdown(f"- {line}")
        if payload.get("headroom_note"):
            st.info(payload["headroom_note"])
        _render_estimate_block(estimate)
    else:
        st.info("Paste a prompt and click **Analyze prompt & forecast cost**, or tune sliders manually.")
