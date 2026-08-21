# Release Process

This checklist separates code publication, hosted-service deployment, registry publication, and marketplace review. Completing one step is not proof that another step completed.

## 1. Pre-release safety review

- Confirm the repository contains no credentials, personal data, internal identifiers, private endpoints, or proprietary backend code.
- Confirm the only MCP endpoint in every manifest is `https://api.vucar.vn/mcp`.
- Review every changed file and the complete Git history intended for publication.
- Confirm Vucar owns or has permission to publish every asset.
- Obtain legal review for [PRIVACY.md](../PRIVACY.md) and [TERMS.md](../TERMS.md) before first production publication.

## 2. Offline validation

```sh
python3 scripts/validate_repository.py
python3 -m unittest discover -s tests -v
claude plugin validate . --strict
claude plugin validate ./plugins/vucar --strict
claude plugin tag ./plugins/vucar --dry-run
mcp-publisher validate
```

All commands must pass from a clean checkout. The repository CI additionally installs the marketplace into disposable Claude Code and Codex profiles so schema-only success is not mistaken for installability.

## 3. Hosted endpoint gate

Deploy the private server through Vucar's normal reviewed deployment process. Do not publish this repository merely because a backend pull request exists.

Verify production independently:

```sh
python3 scripts/smoke_test_mcp.py
```

The smoke test must confirm initialization, exactly three expected tools, read-only annotations, and no authentication requirement. It exercises six valid requests and seven invalid or abuse-oriented boundaries before marketplace submission.

## 4. Publish the repository

1. Create a new public repository with no inherited private history.
2. Push `main` only after the safety review.
3. Enable branch protection, required validation checks, secret scanning, dependency alerts, and private vulnerability reporting.
4. Create the Claude-compatible plugin tag `vucar--v1.0.1` and a GitHub release after the endpoint gate passes.

## 5. Test installations

Use clean client profiles or disposable environments.

```sh
codex plugin marketplace add jakelongvu-bot/Vucar-AI-Plugin
codex plugin add vucar@vucar

claude plugin marketplace add jakelongvu-bot/Vucar-AI-Plugin
claude plugin install vucar@vucar
```

Start a new client session, discover the tools, and run a catalog search, one estimate, and one comparison. Confirm neither client requests credentials.

## 6. MCP Registry

Validate `server.json`, authenticate the publisher with the `io.github.vucarvn` namespace, and publish the immutable `1.0.1` version using the official MCP publisher. Confirm the server appears in the Registry before announcing completion.

## 7. Marketplace submissions

Prepare the evidence listed in [MARKETPLACE-SUBMISSION.md](MARKETPLACE-SUBMISSION.md). Marketplace submission starts a review; it is not approval. Record the submission identifier and later verify the actual public listing in each product.

## 8. Release notes and rollback

- Publish release notes with capabilities, privacy boundary, compatibility, and validation evidence.
- Keep the hosted-service kill switch available for abuse or data-boundary regressions.
- Marketplace metadata can be reverted with a new patch version; an MCP Registry version cannot be overwritten.
- If the endpoint is disabled, update the public status and support issue before announcing recovery.
