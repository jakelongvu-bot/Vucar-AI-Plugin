# Vucar Agent Plugins

Official, public integrations for Vucar's read-only vehicle intelligence MCP server.

This repository contains the same narrowly scoped plugin for Codex and Claude Code, plus the metadata used to publish the remote server to the official MCP Registry. It contains only public configuration, documentation, branding, and validation code. Vucar's proprietary backend is not included.

## What the plugin can do

- Search the public vehicle catalog for supported makes, models, variants, and related taxonomy.
- Estimate an indicative used-car value from vehicle attributes such as make, model, year, and mileage.
- Compare indicative values for multiple vehicles.

Every capability is read-only. The plugin cannot access customer records, employee systems, leads, phone numbers, bookings, inspections, auctions, bids, payments, or internal analytics. It cannot create or change data.

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
│   ├── .mcp.json                          # Claude Code MCP configuration
│   ├── LICENSE, NOTICE, SECURITY.md        # Files retained in installed copies
│   └── assets/                            # Public plugin artwork
├── server.json                            # Official MCP Registry metadata
├── scripts/                               # Offline and live validation
└── tests/                                 # Deterministic metadata tests
```

Codex's manifest points to the same direct-map `.mcp.json` file that Claude Code loads. Repository validation checks that this shared client configuration and the MCP Registry metadata resolve to the exact same endpoint.

## Validate locally

The standard validation path is offline and deterministic:

```sh
python3 scripts/validate_repository.py
python3 -m unittest discover -s tests -v
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
- Tool inputs are limited to non-sensitive vehicle attributes.
- Outputs are indicative estimates, not purchase offers, appraisals, or financial advice.
- Server-side rate limits and abuse controls may reject excessive traffic.
- Do not include names, phone numbers, addresses, account identifiers, or other personal data in tool inputs.

See [PRIVACY.md](PRIVACY.md), [TERMS.md](TERMS.md), and [SECURITY.md](SECURITY.md).

## Release status

Version `1.0.1` adds canonical catalog validation, non-reflective comparison labels, and stronger upstream abuse controls for public-directory review. Publish it only after the matching production endpoint has passed the protocol and abuse-boundary gate. Marketplace, directory, and MCP Registry publication remain separate external review steps; see [docs/RELEASE.md](docs/RELEASE.md).

## License

The repository's code and documentation are licensed under Apache License 2.0. Vucar names, logos, and marks are not licensed for unrelated use; see [NOTICE](NOTICE).
