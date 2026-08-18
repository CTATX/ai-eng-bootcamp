"""Jake — service advisor hypothesis from shop history. No LLM in this cut."""

from __future__ import annotations

import pandas as pd
import requests
import streamlit as st

from api_client import API_BASE, server_is_up


def tag_badge(tag: str) -> str:
    colors = {"FACT": "green", "INFERRED": "orange", "UNKNOWN": "gray"}
    return f":{colors.get(tag, 'blue')}[{tag}]"


@st.cache_data(ttl=10, show_spinner=False)
def post_hypothesis(payload: dict) -> dict:
    response = requests.post(f"{API_BASE}/advisor/hypothesis", json=payload, timeout=30)
    response.raise_for_status()
    return response.json()


st.title("Jake — service advisor")
st.caption(
    "AutoZyte · Powered by FerdAI · FACT / INFERRED / UNKNOWN — no silent fill. "
    "Synthetic Porsche works without a ShopMonkey key."
)

if not server_is_up():
    st.error("API not running. Start with `./start.sh`, then refresh.")
    st.stop()

with st.form("jake_intake"):
    st.subheader("Intake")
    vin = st.text_input("VIN (best match)", placeholder="SYNWP020140002")
    col1, col2, col3 = st.columns(3)
    with col1:
        year = st.number_input("Year (if no VIN)", min_value=1980, max_value=2026, value=2014)
    with col2:
        make = st.text_input("Make", value="Porsche")
    with col3:
        model = st.text_input("Model", placeholder="911")
    engine = st.text_input("Engine / submodel (optional)", placeholder="flat-6")
    complaint = st.text_area(
        "Customer complaint (optional — boosts matching reasons)",
        placeholder="Oil leak, smells like gas, AOS noise…",
    )
    mileage = st.number_input("Mileage (optional — logged but not matched yet)", min_value=0, value=0)
    submitted = st.form_submit_button("Build hypothesis", type="primary")

if not submitted:
    st.info(
        "Try a synthetic VIN from the warehouse, e.g. `SYNWP020140002` (2014 911), "
        "or YMM if you know the car."
    )
    st.stop()

body: dict = {}
if vin.strip():
    body["vin"] = vin.strip()
else:
    body["year"] = int(year)
    body["make"] = make.strip() or None
    body["model"] = model.strip() or None
if engine.strip():
    body["engine"] = engine.strip()
if complaint.strip():
    body["complaint"] = complaint.strip()
if mileage > 0:
    body["mileage"] = int(mileage)

try:
    packet = post_hypothesis(body)
except requests.HTTPError as exc:
    st.error(f"Hypothesis failed: {exc.response.text if exc.response else exc}")
    st.stop()
except requests.RequestException as exc:
    st.error(f"Could not reach API: {exc}")
    st.stop()

st.success(packet.get("persona", "Jake"))
vm = packet["vehicle_match"]
st.markdown(
    f"**Vehicle** {tag_badge(vm.get('tag', 'UNKNOWN'))} — "
    f"{vm.get('identity') or 'No match'} · _{vm.get('note', '')}_"
)

evidence = packet["evidence"]
st.caption(
    f"{tag_badge(evidence.get('tag', 'UNKNOWN'))} "
    f"{evidence.get('order_count', 0)} orders"
    + (
        f" · {evidence.get('date_start')} → {evidence.get('date_end')}"
        if evidence.get("date_start")
        else ""
    )
)

likelihood = packet["likelihood"]
st.subheader("Likelihood")
st.markdown(f"{tag_badge(likelihood.get('tag', 'UNKNOWN'))} {likelihood.get('statement', '')}")
if likelihood.get("selected_reason"):
    c1, c2, c3 = st.columns(3)
    c1.metric("Top reason", likelihood["selected_reason"])
    c2.metric("Share", f"{likelihood.get('percent', '—')}%")
    c3.metric("n", likelihood.get("n", "—"))
    st.caption(f"Best: {likelihood.get('best_case')} · Worst: {likelihood.get('worst_case')}")

left, right = st.columns(2)
with left:
    st.subheader("Ticket")
    ticket = packet["ticket"]
    st.markdown(f"{tag_badge(ticket.get('tag', 'UNKNOWN'))} {ticket.get('method', '')}")
    if ticket.get("typical_usd") is not None:
        st.metric("Typical $", f"${ticket['typical_usd']:,.0f}")
        st.caption(
            f"Observed range ${ticket.get('best_observed_usd')} – ${ticket.get('worst_observed_usd')} "
            f"(n={ticket.get('n_with_amount')})"
        )
    else:
        st.warning("No ticket amounts in warehouse for this match.")

with right:
    st.subheader("Time")
    time_block = packet["time"]
    st.markdown(f"{tag_badge(time_block.get('tag', 'UNKNOWN'))} {time_block.get('note', '')}")
    if time_block.get("typical_hours") is not None:
        st.metric("Typical hours", time_block["typical_hours"])
    else:
        st.warning("No labor hours recorded for this match.")

st.subheader("Common reasons")
if packet["common_reasons"]:
    reasons_df = pd.DataFrame(packet["common_reasons"])
    st.dataframe(
        reasons_df[["label", "order_count", "share", "tag"]].rename(
            columns={"label": "Reason", "order_count": "Orders", "share": "Share", "tag": "Tag"}
        ),
        hide_index=True,
    )
else:
    st.warning("No service reasons in warehouse for this vehicle.")

st.subheader("Parts (for top reason)")
if packet["parts"]:
    parts_df = pd.DataFrame(packet["parts"])
    st.dataframe(
        parts_df[["name", "sku", "times_sold", "avg_part_cost_usd", "tag"]].rename(
            columns={
                "name": "Part",
                "sku": "SKU",
                "times_sold": "Times sold",
                "avg_part_cost_usd": "Avg $",
                "tag": "Tag",
            }
        ),
        hide_index=True,
    )
else:
    st.caption("No parts lines for the selected reason.")

if packet["gotchas"]:
    st.subheader("Gotchas")
    st.dataframe(pd.DataFrame(packet["gotchas"]), hide_index=True)

if packet["recommendations"]:
    st.subheader("Recommendations (advisor-only)")
    for rec in packet["recommendations"]:
        st.markdown(f"- {tag_badge(rec.get('tag', 'UNKNOWN'))} **{rec['action']}** — {rec['because']}")

st.subheader("Not in data")
for gap in packet.get("not_in_data", []):
    st.markdown(f"- **{gap['topic']}** — {gap['why']}")

st.caption(packet.get("guardrail", {}).get("human_gate", ""))

with st.expander("Raw briefing JSON"):
    st.json(packet)
