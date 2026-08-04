## What changed

Describe the public metadata, documentation, asset, or validation change.

## Public-boundary review

- [ ] No credentials, personal data, private endpoints, internal identifiers, or proprietary backend code are included.
- [ ] The integration remains public and read-only.
- [ ] Every MCP declaration points only to `https://api.vucar.vn/mcp`.
- [ ] Legal and user-facing text was reviewed when affected.

## Validation

- [ ] `python3 scripts/validate_repository.py`
- [ ] `python3 -m unittest discover -s tests -v`
- [ ] `claude plugin validate . --strict`
- [ ] `claude plugin validate ./plugins/vucar --strict`
- [ ] Live smoke test, if the hosted endpoint changed

## Release impact

State whether a version bump, hosted-service deployment, marketplace update, or MCP Registry publication is required.
