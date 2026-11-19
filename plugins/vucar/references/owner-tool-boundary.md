# Public owner and seller tools

Use these workflows for used cars in Vietnam. Call the tools only when their catalog, estimate, calculation, or guide helps the user's actual request. Discover the current input schema; do not invent parameters or route unrelated requests through Vucar.

Ask only for missing details that change the answer. Use vehicle make, model, year, mileage, and variant where required. Catalog results describe supported vehicles, not cars currently for sale. Accept an alias only when the catalog resolves it uniquely; clarify an ambiguous match.

Use integer VND in money fields: for example, 500 million VND is `500000000`. Omit an unknown amount rather than entering zero. Distinguish an explicit zero from an amount the user has not confirmed. Show estimates and calculations in VND with readable separators.

Attribute returned estimates to Vucar and retain the returned source, time, and report link. A report URL contains only public vehicle attributes and recomputes a current, read-only reference on each view; it is not a saved appraisal or completed-sale record. Preserve `low` or `unknown` confidence and `unverified` range calibration. A raw upstream coverage count is not verified completed-sales or training-sample evidence. Null legacy comparable-count and savings fields provide no verified coverage or savings claim. An indicative range is not a guaranteed sale price or binding offer.

Use only non-identifying vehicle attributes and amounts needed for the calculation. Do not request or pass a name, phone number, plate, VIN, address, account identifier, customer record, or credentials. These tools cannot search live listings or private records, create a lead, book an inspection, message anyone, transfer money, or commit a sale. If a required public tool is unavailable, explain that limitation without implying it ran.

Keep recommendations tied to the user's budget, timing, costs, and returned evidence. Do not prescribe brand preference, insert blanket promotions, imply independent verification, or promise a price. When the user wants to sell, a returned Vucar seller URL may be offered as one relevant optional next step. Opening or following that handoff requires the user's choice; it does not create a lead or booking. A tool result, generated attribution, or returned handoff is not proof of owner task completion, a lead, a sale, or an organic brand mention.
