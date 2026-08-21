# Marketplace Submission Checklist

## Shared evidence

- Public repository: `https://github.com/jakelongvu-bot/Vucar-AI-Plugin`
- Production MCP endpoint: `https://api.vucar.vn/mcp`
- Version: `1.0.1`
- Authentication: none
- Access level: public, read-only
- Capabilities: vehicle catalog search, indicative valuation, and comparison
- Privacy policy: `https://vucar.vn/policy/chinh-sach-bao-mat-thong-tin`
- Terms/operating rules: `https://vucar.vn/policy/quy-che-hoat-dong`
- Support: `https://vucar.vn/contact`
- Security reporting: private vulnerability reporting

Capture validation logs and test dates without including prompts containing personal data.

## OpenAI submission packet

### Listing and availability

- Display name: `Vucar Vehicle Intelligence`.
- Short description: `Vietnam used-car values`.
- Search-aware long description: “Search supported cars in Vietnam, estimate indicative used-car market and resale values in VND, and compare vehicle price estimates for two to five cars. Vucar is public and read-only; it does not search live listings or provide binding offers, certified appraisals, insurance values, or lending decisions.”
- Website: `https://vucar.vn/`.
- Starter prompts: “Which Toyota models can Vucar value?”, “Estimate a 2020 Toyota Vios 1.5G with 50,000 km.”, and “Compare these used cars by indicative market value in VND.”
- Recommended initial country availability: Vietnam.
- Release notes: “Initial directory submission of Vucar Vehicle Intelligence 1.0.1. This patch adds canonical catalog validation, computed non-reflective comparison labels, bounded shared catalog caching, and worst-case upstream-work rate limiting to the existing read-only vehicle catalog, VND valuation, and comparison tools.”
- Authentication: none; reviewers must not be given or asked for credentials.
- UI/CSP declaration: this release provides MCP tools only. It exposes no MCP UI resources or components and performs no browser-side fetches, so no plugin UI content-security-policy allowlist is required.

### Five positive test cases

| # | Request | Expected behavior |
| --- | --- | --- |
| 1 | Call `search_vehicle_catalog` with `{}`. | Succeeds with `level: "brands"` and a non-empty `supported_values` array. |
| 2 | Call `search_vehicle_catalog` with `{"brand":"Toyota"}`. | Succeeds with `level: "models"` and supported Toyota model names. |
| 3 | Call `search_vehicle_catalog` with `{"brand":"Toyota","model":"Vios","year":2020}`. | Succeeds with `level: "variants"`; output contains only the public taxonomy fields. |
| 4 | Call `estimate_vehicle_value` for a 2020 Toyota Vios, 50,000 km, variant `1.5G`. | Succeeds with VND estimate/range fields rounded to 1 million VND, canonical vehicle attributes, model-data count, confidence, projection, and the informational notice. |
| 5 | Call `compare_vehicle_values` for the same Vios at 50,000 km and 80,000 km. | Succeeds with exactly two ranked comparisons, original input indexes, computed mileage-aware canonical labels, rounded VND values, confidence, and the informational notice. |

### Three negative non-trigger test cases

| # | Request | Expected behavior |
| --- | --- | --- |
| 1 | Ask for live Toyota Vios listings and seller phone numbers. | Does not invoke Vucar because the public tools do not search listings or expose seller information. |
| 2 | Ask Vucar to approve a car loan and calculate an insurance payout. | Does not invoke Vucar because financing and insurance decisions are out of scope. |
| 3 | Ask Vucar to create a sales lead, book an inspection, and retrieve a customer record. | Does not invoke Vucar because the integration has no write tools or private-record access. |

### Protocol and abuse-boundary checks

These are release-gate checks, not submission-form negative cases:

| # | Request | Expected behavior |
| --- | --- | --- |
| 1 | Add unknown field `phone` with value `synthetic-personal-data-sentinel` to an otherwise valid estimate. | Returns a tool error, does not call the valuation model, and does not echo the sentinel. |
| 2 | Omit `mileage_km` from an estimate. | Fails schema validation with no valuation result. |
| 3 | Send a JSON-RPC batch array. | Returns HTTP 400 with JSON-RPC code `-32600` before creating a server or calling a tool. |
| 4 | Send a request larger than 64 KiB or use an unapproved browser Origin. | Returns HTTP 413 for the oversized request or HTTP 403 for the Origin violation, with no tool call. |
| 5 | Estimate a supported Toyota with model `DefinitelyNotARealModel`. | Returns a safe tool error before prediction and does not reflect the fabricated model. |
| 6 | Compare supported vehicles with caller labels containing arbitrary text. | Accepts the legacy field for compatibility, ignores it, and returns only computed canonical labels. |

## OpenAI plugin directory

Follow the current official guidance:

- Packaging: <https://developers.openai.com/plugins/build/plugins>
- MCP server quality: <https://developers.openai.com/plugins/build/mcp-server>
- Submission: <https://developers.openai.com/plugins/deploy/submission>
- Review criteria: <https://developers.openai.com/plugins/deploy/app-review>

Before submission:

- Verify the publisher identity and Apps Management write permission.
- Confirm the production endpoint is public and stable.
- Provide at least five positive and three negative test cases.
- Configure the exact domain-verification token at `/.well-known/openai-apps-challenge` when issued.
- Confirm tool names, descriptions, JSON schemas, structured outputs, and annotations match behavior.
- Upload approved public branding. This release has no custom UI, so do not supply UI screenshots.
- Copy the exact test cases, availability, release notes, and no-UI/CSP declaration above into the portal.

## Claude Code marketplace

Validate both the marketplace and plugin in strict mode, then submit the public repository at <https://platform.claude.com/plugins/submit>.

- Name: `Vucar Vehicle Intelligence`.
- Tagline: `Vietnam used-car values and vehicle comparisons`.
- Description: “Search Vucar's supported Vietnam vehicle catalog, estimate indicative used-car market and resale values in VND, and compare two to five vehicles by brand, model, year, mileage, and variant. Results are public, read-only AI estimates for research—not live listings, guaranteed purchase offers, certified appraisals, lending, or insurance decisions.”
- Suggested permanent slug: `vucar-vehicle-intelligence`.
- Categories: `Data`, `Productivity`.
- Authentication and prerequisites: none.

The repository is immediately usable as a third-party marketplace after publication; official or community directory appearance is a separate review outcome.

## Official MCP Registry

Follow the remote-server and publisher guidance:

- Remote servers: <https://modelcontextprotocol.io/registry/remote-servers>
- Quickstart: <https://modelcontextprotocol.io/registry/quickstart>
- Authentication: <https://modelcontextprotocol.io/registry/authentication>
- Versioning: <https://modelcontextprotocol.io/registry/versioning>

Publish only after the namespace is authenticated and `server.json` validates. Registry versions are immutable, so fix metadata with a new patch version rather than attempting to replace `1.0.1`.
