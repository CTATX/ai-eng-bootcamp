# AI FinOps KPI contract

**Status:** MVP v0.1 · **Scope:** OpenAI `/ask` usage · **Owner:** CT

The product is an **AI unit economics and operations control plane**, not a spend-only dashboard.
Spend never stands in for value, productivity, quality, or ROI.

## MVP jobs

- Business owner: determine whether a use case creates enough validated value to continue funding.
- AI product owner: optimize cost per accepted outcome while preserving quality and reliability.
- AI Ops / FinOps: attribute usage, forecast budget risk, identify waste, and enforce scoped controls.
- Individual user: understand usage and improve outcomes; individual metrics are not performance rankings.

## KPI definitions

| KPI | Definition |
|-----|------------|
| Actual API spend | Sum of cost calculated from provider-reported token usage and the configured price schedule. Labeled **estimated** until reconciled to provider invoices. |
| Average daily spend | Spend in the selected window divided by all calendar days in that window, including zero-spend days. |
| Budget utilization | Month-to-date estimated API spend divided by approved monthly budget. |
| Projected month-end spend | Month-to-date spend divided by elapsed calendar days, multiplied by days in month. Directional, not a commitment. |
| Successful task rate | Successful API calls divided by attempted API calls. |
| Acceptance rate | Accepted outputs divided by reviewed outputs. Pending outputs are excluded. |
| AI cost per accepted outcome | Attributable API spend divided by accepted outcomes. |
| Provider-reported cache ratio | Cached input tokens divided by total input tokens. This is not cross-provider normalized. |
| Normalized cache ratio | Cached input tokens divided by cache-eligible input tokens. Not available until providers expose a comparable denominator. |
| Capacity value | Verified hours avoided or redeployed multiplied by an approved loaded hourly rate. Never call this cash savings unless expenditure was removed. |
| Total cost to serve | API cost + AI licenses + infrastructure + people cost. MVP currently captures API cost only. |
| Value-to-cost ratio | Finance-validated gross value divided by total cost to serve. Not shown as validated until value and cost coverage are complete. |
| Optimal usage | Lowest total cost per accepted outcome that meets explicit quality, latency, reliability, and risk thresholds. |

## Attribution contract

Every billable call carries:

- `user_id`
- `business_owner_id`
- `use_case`
- `environment`
- provider and model
- request ID and timestamp

Untagged production usage must eventually be quarantined. The MVP supplies explicit local defaults so learning can continue.

## Controls

| Level | Default behavior |
|-------|------------------|
| 50% of daily budget | Informational in-app notification |
| 80% of daily budget | Warning |
| 100% of daily budget | Critical alert |
| Hard stop | Off by default; when enabled, blocks new `/ask` calls after the scoped daily cap is reached |

Production and safety-critical workloads should degrade gracefully or require approval rather than stop abruptly.
Overrides must eventually record approver, reason, new cap, and expiry.

## MVP data confidence

- Provider tokens: **provider reported**
- API cost: **estimated from configured pricing**
- Cache ratio: **provider reported, not normalized**
- Accepted outcome: **user reviewed**
- Capacity value: **unverified assumption**
- ROI / value-to-cost: **withheld until total cost and value are validated**

## Build sequence

1. Record every `/ask` call and provider usage.
2. Expose spend, cache, reliability, and outcome KPIs.
3. Add a dashboard with attribution and budget state.
4. Add user-reviewed accepted/rejected outcomes.
5. Add business-owner value assumptions and validation workflow.
6. Add external notifications, scoped budgets, audited overrides, and invoice reconciliation.
