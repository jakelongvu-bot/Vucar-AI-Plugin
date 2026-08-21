# Vucar

Vucar adds public, read-only vehicle intelligence to Codex and Claude Code.

## Available capabilities

The server intentionally exposes only three capability groups:

1. Vehicle catalog search for supported makes, models, variants, and related taxonomy.
2. Indicative used-car value estimation from non-sensitive vehicle attributes.
3. Side-by-side comparison of indicative values for multiple vehicles.

Tool names and schemas are discovered directly from the MCP server. Treat estimates as informational ranges, not binding offers or professional appraisals.

The server validates vehicle identity against its public catalog, rounds values to the nearest 1 million VND to avoid false precision, and returns a low-confidence warning when no comparable vehicles are present in the model data.

## Example requests

- “Which Toyota models are supported?”
- “Estimate the value of a 2020 Toyota Vios with 50,000 km.”
- “Compare these three used cars by indicative value.”

## Data boundary

The plugin does not provide customer, employee, dealer, lead, booking, inspection, auction, bid, payment, messaging, or internal reporting access. It has no write tools.

Do not place personal data in vehicle-description fields. Report unexpected access or behavior according to the bundled [security policy](SECURITY.md).
