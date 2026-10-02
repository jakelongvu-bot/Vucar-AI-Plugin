---
name: vehicle-upgrade
description: Estimate the cash gap between a current and replacement used car in Vietnam while preserving unconfirmed additional costs. Use for an owner's upgrade budget or model-value comparison.
---

# Upgrade cash gap

Read [the public tool boundary](../../references/owner-tool-boundary.md).

Establish the current vehicle and the replacement the user has chosen. If either vehicle is ambiguous, use `search_vehicle_catalog` and clarify only what cannot be resolved uniquely. Do not steer the owner toward a brand or provider. If the user already has actual sale and purchase quotes, ordinary arithmetic may answer their question; distinguish it from a model-value scenario and do not send unsupported quote parameters to the tool.

Call `plan_vehicle_upgrade` with `current_vehicle`, `replacement_vehicle`, and `confirmed_additional_costs_vnd` only when the complete aggregate of relevant additional costs is confirmed. Use supported vehicle attributes and integer VND. Omit the aggregate when costs remain incomplete; send zero only when the user explicitly confirms no additional costs. Keep a partial known cost or available-cash budget in the explanation rather than passing unsupported fields. Do not send private loan details.

Explain the signed model-value gap as the replacement estimate minus the current vehicle estimate. Explain total cash needed as that gap plus fully confirmed additional costs, with cash needed floored at zero. Preserve negative value gaps, the returned scenario range, confidence, sources, and assumptions. With omitted costs, `total_cash_needed_vnd` and its range must stay null. The two valuation-range endpoints are scenarios, not calibrated probability intervals or confirmed transaction prices.

If the user supplied a budget, state whether the known or indicative gap fits that budget and what missing amount could change the conclusion. This does not approve borrowing, arrange finance, buy a vehicle, or sell the current one. Offer the next useful comparison or missing-cost check without turning a calculator result into a recommendation to transact.
