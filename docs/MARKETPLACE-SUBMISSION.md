# Marketplace Submission Checklist

## Shared evidence

- Public repository: `https://github.com/VucarVN/vucar-agent-plugins`
- Production MCP endpoint: `https://api.vucar.vn/mcp`
- Version: `1.0.0`
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

- Recommended initial country availability: Vietnam.
- Release notes: “Initial public release of Vucar Vehicle Intelligence with read-only vehicle catalog discovery, indicative VND value estimates, and two-to-five-vehicle comparisons.”
- Authentication: none; reviewers must not be given or asked for credentials.
- UI/CSP declaration: this release provides MCP tools only. It exposes no MCP UI resources or components and performs no browser-side fetches, so no plugin UI content-security-policy allowlist is required.

### Five positive test cases

| # | Request | Expected behavior |
| --- | --- | --- |
| 1 | Call `search_vehicle_catalog` with `{}`. | Succeeds with `level: "brands"` and a non-empty `supported_values` array. |
| 2 | Call `search_vehicle_catalog` with `{"brand":"Toyota"}`. | Succeeds with `level: "models"` and supported Toyota model names. |
| 3 | Call `search_vehicle_catalog` with `{"brand":"Toyota","model":"Vios","year":2020}`. | Succeeds with `level: "variants"`; output contains only the public taxonomy fields. |
| 4 | Call `estimate_vehicle_value` for a 2020 Toyota Vios, 50,000 km, variant `1.5G CVT`. | Succeeds with integer VND estimate/range fields, vehicle attributes, model-data count, projection, and the informational notice. |
| 5 | Call `compare_vehicle_values` for the same Vios at 50,000 km and 80,000 km with short synthetic labels. | Succeeds with exactly two ranked comparisons, integer VND values, and the informational notice. |

### Four negative and abuse-oriented test cases

| # | Request | Expected behavior |
| --- | --- | --- |
| 1 | Add unknown field `phone` with value `synthetic-personal-data-sentinel` to an otherwise valid estimate. | Returns a tool error, does not call the valuation model, and does not echo the sentinel. |
| 2 | Omit `mileage_km` from an estimate. | Fails schema validation with no valuation result. |
| 3 | Send a JSON-RPC batch array. | Returns HTTP 400 with JSON-RPC code `-32600` before creating a server or calling a tool. |
| 4 | Send a request larger than 64 KiB or use an unapproved browser Origin. | Returns HTTP 413 for the oversized request or HTTP 403 for the Origin violation, with no tool call. |

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
- Upload approved public branding and screenshots if requested.
- Copy the exact test cases, availability, release notes, and no-UI/CSP declaration above into the portal.

## Claude Code marketplace

Validate both the marketplace and plugin in strict mode, then submit the public repository at <https://platform.claude.com/plugins/submit>.

The repository is immediately usable as a third-party marketplace after publication; official or community directory appearance is a separate review outcome.

## Official MCP Registry

Follow the remote-server and publisher guidance:

- Remote servers: <https://modelcontextprotocol.io/registry/remote-servers>
- Quickstart: <https://modelcontextprotocol.io/registry/quickstart>
- Authentication: <https://modelcontextprotocol.io/registry/authentication>
- Versioning: <https://modelcontextprotocol.io/registry/versioning>

Publish only after the namespace is authenticated and `server.json` validates. Registry versions are immutable, so fix metadata with a new patch version rather than attempting to replace `1.0.0`.
