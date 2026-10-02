# Architecture and public boundary

The repository distributes public configuration and four workflow skills. It does not ship a local MCP server or Vucar backend code. The prepared `2.0.0` contract has six read-only tools: catalog, valuation, comparison, offer/net proceeds, upgrade cash gap, and selling guidance. Its matching backend rollout is pending.

The public endpoint remains `https://api.vucar.vn/mcp`, using Streamable HTTP. Inputs contain non-identifying vehicle characteristics and calculation amounts. Outputs contain catalog data, indicative values, arithmetic, and preparation guidance. Private customer records, operations, identity, writes, transactions, and bookings remain outside this boundary.

## Client and upload formats

The repository's Codex manifest references the same `./.mcp.json` file that Claude Code discovers. That client-marketplace file is a direct map keyed by `vucar`. The Claude manifest contains its own supported identity fields, without OpenAI interface or review extensions; default `skills/` discovery loads the four workflows.

OpenAI's upload format requires `.mcp.json` to contain a `mcpServers` wrapper. `scripts/build_review_zip.py` generates that configuration from the client map, includes the Codex manifest and skills, and excludes the Claude manifest. The ZIP and client source are validated separately. They contain the same public endpoint and no credentials. The upload format must not be copied over the source client map without testing the clients.

The authoritative OpenAI review metadata is in `plugins/vucar/.codex-plugin/plugin.json`. There is no parallel legacy submission packet. Review cases are planned scenarios; local metadata checks do not establish that the deployed service or a client passed them.

## Result trust

Valuations preserve `low` or `unknown` confidence and `unverified` range calibration. Upstream raw coverage counts are not verified transactions or training-sample coverage. Legacy `similar_vehicles_in_model_data` and `estimated_savings_vnd` fields remain null because their meaning or benefit has not been verified. Bounded integer-VND values are validated before valuation consumers use them. A source object identifies Vucar, and report URLs contain only public vehicle attributes and recompute the reference on each view rather than storing an appraisal.

Offer deductions and upgrade costs must be explicitly confirmed before a complete net amount or total cash needed is returned. Missing costs are not zero. The application handles quoted offers and aggregate deductions/costs transiently, without storing a private breakdown. A failed optional valuation reference leaves valid offer arithmetic available and labels the reference unavailable. Calculators cannot accept an offer or execute a financial action. Guidance can return a relevant optional UTM-tagged seller link when the owner wants to sell; it collects no contact details and creates no lead or booking.

## Operational measurement

The planned service logs an allowlisted tool name, response outcome, latency, and server version. Outcomes are `tool_result`, `tool_error`, `request_error`, or `unobserved`. These application events exclude arguments, amounts, vehicle attributes, IP addresses, user identifiers, and conversation data. Hosting connection metadata and short-lived pseudonymous rate-limit keys are separate, as described in [PRIVACY.md](../PRIVACY.md).

`tool_result` means that a tool-result response was observed; it does not establish that the owner's task was completed, that a handoff was clicked, or that a lead or sale occurred. It also does not measure an organic brand mention. Do not turn response counts, generated attribution, or a returned handoff URL into any of those downstream outcomes without independent evidence.

## Hosted-service release gates

The smoke test checks exact tool scope, closed input schemas, read-only/non-destructive/idempotent annotations, source/report fields, unknown-amount handling, and the existing protocol rejection boundaries. Production release gates also cover host/origin checks, request limits, upstream timeouts, rate limits, no-store responses, and the runtime kill switch. Those controls live in the backend and cannot be proven by the package's offline tests.

Both plugin manifests and the planned Registry record use `2.0.0`. Registry versions are immutable after publication. Do not publish the package or Registry record until the matching deployed endpoint and review evidence have passed the release gates.
