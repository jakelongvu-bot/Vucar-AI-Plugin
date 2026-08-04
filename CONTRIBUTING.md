# Contributing

Thank you for improving Vucar's public agent integrations.

## Public boundary

This repository is intentionally limited to public plugin metadata, documentation, artwork, and validation code. Do not contribute:

- Customer, employee, dealer, lead, booking, inspection, auction, bid, payment, or messaging data.
- Names, phone numbers, email addresses, addresses, identifiers, or realistic personal-data fixtures.
- Credentials, tokens, cookies, environment files, connection strings, or private endpoints.
- Internal architecture, database schemas, runbooks, source code, metrics, or incident details.
- Write tools or authenticated operational capabilities.

Backend changes belong in Vucar's private development process and must undergo separate review.

## Development workflow

1. Create a focused branch from `main`.
2. Update all version-bearing manifests together for a release.
3. Run the offline validator and unit tests.
4. Run Claude Code's strict validators when changing Claude metadata.
5. Run the live MCP smoke test only against the documented public endpoint.
6. Describe security and compatibility implications in the pull request.

```sh
python3 scripts/validate_repository.py
python3 -m unittest discover -s tests -v
claude plugin validate . --strict
claude plugin validate ./plugins/vucar --strict
```

## Pull requests

Keep changes small and reviewable. A pull request must explain what changed, why it is safe for public distribution, how it was validated, and whether a hosted-service deployment is required before release.

Contributions are licensed under Apache License 2.0 unless clearly marked otherwise.
