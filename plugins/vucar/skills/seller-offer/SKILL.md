---
name: seller-offer
description: Compare a used-car offer with an indicative Vietnam valuation and calculate the owner's net proceeds from supplied deductions. Use when evaluating an offer or what the owner would receive after a sale.
---

# Seller offer and net proceeds

Read [the public tool boundary](../../references/owner-tool-boundary.md).

Reuse the offered price and vehicle details already given. For pure proceeds arithmetic, vehicle details are unnecessary; include the optional vehicle only when the owner wants an indicative value comparison. Ask for a missing offer amount before assessing it. A seller's asking price is separate; do not substitute it for an actual offer. Do not request the lender, contract, or owner's identity.

Call `check_seller_offer` with `gross_offer_vnd`, `deductions_status`, and the aggregate `confirmed_deductions_vnd` when supplied. Combine known loan payoff and costs locally; send only their total, without a private breakdown. Use `unknown` when deductions are incomplete, `known` only when the full total is confirmed, and `none` only when the user confirms no deductions. A partial known aggregate may accompany `unknown`, but final `net_proceeds_vnd` must remain null. Do not infer fees or treat omission as zero. If the user wants a complete net amount, ask one concise question about the material missing deductions.

Explain how the offer relates to the returned indicative range and its uncertainty. Show the additive bridge: gross offer minus known deductions equals the provisional amount after known deductions. Label a final net amount only when the tool confirms that all required deductions are known. State whether unresolved fees, debt, or costs could lower that amount, without inventing them.

Keep the owner's timing, condition, and alternatives in view. The model does not accept, negotiate, or bind an offer. If the owner wants help preparing to sell, continue with the sale-preparation workflow; a seller handoff is optional and does not create a customer record.
