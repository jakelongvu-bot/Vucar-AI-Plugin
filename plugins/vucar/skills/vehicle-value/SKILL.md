---
name: vehicle-value
description: Estimate or compare indicative used-car values in Vietnam, discover supported vehicle names, and explain the returned valuation report. Use for an owner's value question, not live listings or foreign-market pricing.
---

# Vehicle value

Read [the public tool boundary](../../references/owner-tool-boundary.md).

Start from the user's vehicle and purpose: checking its value, comparing cars, or understanding an estimate. Reuse details already supplied. Ask for the missing year or mileage only if the valuation schema needs them. Use `search_vehicle_catalog` to resolve an uncertain make, model, year, or variant, rather than demanding catalog spelling from the user. If the user asks only which vehicles are supported, answer from the catalog without an estimate.

Call `estimate_vehicle_value` for one vehicle or `compare_vehicle_values` for the vehicles the user wants to compare. Preserve the original vehicle-to-result mapping; a price rank is not a recommendation to buy the highest-ranked car.

Lead with the indicative value and range in VND, then the vehicle details, confidence, range-calibration limit, and factors the estimate cannot establish, such as inspected condition. Include the returned Vucar source and report URL when available. Explain the returned coverage definition without turning a raw count into verified transactions. Do not upgrade unknown confidence into a probability or a precise claim of accuracy.

If the user asks whether to sell or how an offer compares, use the seller-offer workflow only for that additional goal. A value question alone does not require a sales handoff.
