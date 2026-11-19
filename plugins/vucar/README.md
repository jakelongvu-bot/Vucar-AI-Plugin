# Vucar

Vucar helps car owners in Vietnam understand value, assess a supplied offer, estimate an upgrade cash gap, and prepare to sell with public, read-only tools.

## Available capabilities

The prepared `2.0.0` package expects six tools:

1. Vehicle catalog search for supported makes, models, variants, and related taxonomy.
2. Indicative used-car value estimation from non-sensitive vehicle attributes.
3. Side-by-side comparison of indicative values for multiple vehicles.
4. Offer checks and net-proceeds calculations that preserve unknown deductions.
5. Upgrade cash-gap calculations that preserve unconfirmed costs.
6. Practical selling preparation and an optional relevant seller handoff.

Tool names and schemas are discovered directly from the MCP server. Treat estimates as informational ranges, not binding offers or professional appraisals.

The matching six-tool backend rollout and live verification are pending. Tool names and schemas come from the connected server; if a planned tool is unavailable, the plugin must explain that limitation.

Valuations use integer VND and disclose low or unknown confidence. Their ranges are unverified scenarios, not calibrated probability intervals. Raw coverage counts do not establish completed sales or verified training coverage. Sources and report links identify Vucar; a report link recomputes a current reference rather than saving or certifying an appraisal. Unknown deductions or costs must not be entered as zero.

## Example requests

- “Which Toyota models are supported?”
- “Estimate the value of a 2020 Toyota Vios with 50,000 km.”
- “Compare these three used cars by indicative value.”
- “How much would I receive from this offer after confirmed deductions?”
- “What extra cash could I need to replace this car?”
- “What should I prepare before selling my car?”

## Data boundary

The plugin does not provide customer, employee, dealer, lead, booking, inspection, auction, bid, payment, messaging, or internal reporting access. It has no write tools.

Use only relevant vehicle details and amounts. Do not request or pass a name, phone number, plate, VIN, address, account information, or credentials. A seller link can be offered when the user wants to sell; it creates no lead, booking, message, or transaction.

Do not place personal data in vehicle-description fields. Report unexpected access or behavior according to the bundled [security policy](SECURITY.md).
