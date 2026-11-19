---
name: sale-preparation
description: Help an owner prepare to sell a used car in Vietnam with a practical checklist and the choices that affect timing, condition, documents, and payment. Use for selling preparation, not booking or private-case follow-up.
---

# Sale preparation

Read [the public tool boundary](../../references/owner-tool-boundary.md).

Use the owner's stated objective and timing. General preparation does not need a full vehicle intake. Call `get_selling_guidance` with relevant known options: `goal` (`exploring`, `sell_soon`, or `upgrade`), `condition`, `has_maintenance_records`, and the actual `assistant_source` when known. Do not invent an exact sale deadline parameter or ask for condition details when a general guide suffices. The returned guide is Vietnamese; explain it naturally in the user's language when needed.

Turn the returned guidance into the next few practical actions: prepare non-identifying vehicle details and condition information, identify which documents must be checked privately, compare gross offers with deductions, and confirm payment and handover arrangements before agreeing to a sale. Do not ask the owner to upload identity papers or registration numbers. Preserve any returned limits about inspections, documentation, and general guidance rather than giving a legal guarantee.

If the owner also wants a price, use the vehicle-value workflow. If an offer or loan payoff affects the decision, use the seller-offer workflow. Reuse earlier inputs and keep each tool call tied to that stated goal.

When the user wants to sell and the guide returns `selling_handoff`, its URL can be included once as an optional next step. An `exploring` or `upgrade` response has no selling handoff; do not manufacture one. Describe what the link is for, without claiming an inspection, offer, booking, or lead exists. The owner chooses whether to continue there; this plugin collects no contact details and initiates no external action.
