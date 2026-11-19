# Vucar Agent Plugins

Public, read-only tools for car owners and sellers in Vietnam.

Version `2.0.0` prepares an owner and seller toolkit for Codex, ChatGPT, and Claude Code. The matching backend rollout, live verification, and reviewer video are pending. This repository contains public configuration, four workflow skills, documentation, branding, and validation code. Vucar's backend is not included.

## What the plugin can do

- Search the public vehicle catalog for supported makes, models, variants, and related taxonomy.
- Estimate an indicative used-car value from vehicle attributes such as make, model, year, and mileage.
- Compare indicative values for multiple vehicles.
- Check a supplied offer and calculate net proceeds only when deductions are confirmed.
- Estimate the cash gap between a current vehicle and a replacement, keeping unconfirmed costs open.
- Prepare to sell with a practical checklist and an optional seller handoff when relevant to the user's request.

Every capability is read-only. The plugin cannot access customer records, employee systems, leads, phone numbers, bookings, inspection records, auctions, bids, payments, or internal analytics. It cannot create or change data, accept an offer, arrange finance, or contact anyone. A seller link is an optional handoff; it creates no lead or booking.

Values are in integer VND. Low or unknown confidence and unverified range calibration are disclosed. A raw coverage count is not verified completed-sale or training-sample evidence. Unknown deductions and purchase costs remain unknown; a partial calculation is not a final net amount. Returned report links recompute current valuation references rather than saving an appraisal.

## Install from this marketplace

### Codex

```sh
codex plugin marketplace add jakelongvu-bot/Vucar-AI-Plugin
codex plugin add vucar@vucar
```

### Claude Code

```sh
claude plugin marketplace add https://github.com/jakelongvu-bot/Vucar-AI-Plugin.git
claude plugin install vucar@vucar
```

Both clients connect to the same public Streamable HTTP endpoint:

```text
https://api.vucar.vn/mcp
```

No API key or Vucar account is required for these public, read-only tools.

## Connect without the plugin marketplace

Codex:

```sh
codex mcp add vucar --url https://api.vucar.vn/mcp
```

Claude Code:

```sh
claude mcp add --transport http vucar https://api.vucar.vn/mcp
```

## Repository layout

```text
.
├── .agents/plugins/marketplace.json       # Codex marketplace catalog
├── .claude-plugin/marketplace.json        # Claude Code marketplace catalog
├── plugins/vucar/
│   ├── .codex-plugin/plugin.json          # Codex plugin manifest
│   ├── .claude-plugin/plugin.json         # Claude Code plugin manifest
│   ├── .mcp.json                          # Client marketplace MCP map
│   ├── skills/                           # Four owner and seller workflows
│   ├── references/                       # Shared public-tool boundary
│   ├── LICENSE, NOTICE, PRIVACY.md         # Files retained in installed copies
│   └── assets/                            # Public plugin artwork
├── server.json                            # Official MCP Registry metadata
├── scripts/                               # Offline and live validation
└── tests/                                 # Deterministic metadata tests
```

Codex's client-marketplace manifest points to the same direct-map `.mcp.json` file that Claude Code loads. The OpenAI review ZIP builder wraps that map in `mcpServers`, matching the submission format, and excludes the Claude manifest. The two artifacts declare the same endpoint; their configuration formats are validated separately.

## Validate locally

The standard validation path is offline and deterministic:

```sh
python3 scripts/validate_repository.py
python3 -m unittest discover -s tests -v
python3 scripts/build_review_zip.py --output /tmp/vucar-owner-seller-plugin-2.0.0.zip
```

If Claude Code is installed, also run its strict validators:

```sh
claude plugin validate . --strict
claude plugin validate ./plugins/vucar --strict
claude plugin tag ./plugins/vucar --dry-run
```

The CI release gate also performs clean Claude and Codex marketplace installations and validates `server.json` with the checksum-pinned official MCP Publisher.

After the production endpoint is deployed, run the opt-in protocol smoke test:

```sh
python3 scripts/smoke_test_mcp.py
```

## Safety and privacy

- The endpoint is public and does not accept authentication credentials.
- Tool inputs are limited to non-identifying vehicle attributes and amounts needed for the calculation.
- Outputs are indicative estimates, not purchase offers, appraisals, or financial advice.
- Server-side rate limits and abuse controls may reject excessive traffic.
- Do not include names, phone numbers, addresses, plates, VINs, account identifiers, or other personal data in tool inputs.

See [PRIVACY.md](PRIVACY.md), [TERMS.md](TERMS.md), and [SECURITY.md](SECURITY.md).

## Release status

Version `2.0.0` is a prepared package, not a deployed or published release. Its smoke test expects the matching six-tool backend and will fail against an older server. Before submission, verify the deployed contract, run the five positive and three negative review cases, and provide an accessible video walkthrough. Marketplace, directory, and MCP Registry publication remain separate external review steps; see [docs/RELEASE.md](docs/RELEASE.md).

## License

The repository's code and documentation are licensed under Apache License 2.0. Vucar names, logos, and marks are not licensed for unrelated use; see [NOTICE](NOTICE).
