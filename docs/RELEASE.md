# Release process

Version `2.0.0` is a prepared owner/seller package. Code review, hosted rollout, review execution, an accessible video, submission, and publication are separate steps. None is established by an offline package check.

## Local package validation

Check the public diff for credentials, personal data, private endpoints, obsolete metadata, and unsupported claims. Use the existing repository rather than copying private backend history. Run:

```sh
python3 scripts/validate_repository.py
python3 -m unittest discover -s tests -v
claude plugin validate . --strict
claude plugin validate ./plugins/vucar --strict
claude plugin tag ./plugins/vucar --dry-run
python3 scripts/build_review_zip.py --output /tmp/vucar-owner-seller-plugin-2.0.0.zip
mcp-publisher validate
```

The ZIP builder changes only the artifact's MCP configuration to OpenAI's wrapper format. Validate that artifact independently; do not use it as proof of Claude installation. CI additionally tests clean client ingestion and Registry metadata.

## Matching backend gate

Deploy the backend only through the authorized reviewed process. After deployment, run:

```sh
python3 scripts/smoke_test_mcp.py
```

The smoke script requires server version `2.0.0` and exactly six public read-only tools. It checks sources, reports, unverified ranges, incomplete costs, canonical inputs, and the original batch/origin/body-size/schema rejection boundaries. It intentionally fails against an older server.

Check that application operational events contain only an allowlisted tool name, response outcome, latency, and server version. Confirm arguments, amounts, vehicle details, IP addresses, and conversation data are absent. An observed `tool_result` is response-level evidence; owner completion, handoff clicks, leads, sales, and organic mentions require their own evidence.

Use clean client profiles to install the marketplace. Run the five positive and three negative cases declared in the manifest and verify the actual tool requests/results. Record a real accessible video and add its URL to `extensions.com.openai.review.demo_recording_url`, then rebuild and recheck the ZIP.

## Authorized publication

With explicit authorization, push the reviewed public changes and verify CI. Create the Claude-compatible release tag `vucar--v2.0.0` only after the matching backend gate passes. Validate and publish the immutable `2.0.0` MCP Registry record only when authorized, then check the Registry's actual record.

Follow [MARKETPLACE-SUBMISSION.md](MARKETPLACE-SUBMISSION.md) for OpenAI upload and review. Verify the uploaded package metadata and six scanned tools before submitting. Approval and directory publication require their own verified outcomes. Keep private reviewer credentials in the secure dashboard if authentication is ever introduced.

## Recovery

If the deployed contract fails, use the existing backend rollback or kill-switch procedure with the required authorization. Package metadata can be corrected with a new version; a published Registry version cannot be overwritten. Report the actual endpoint and publication state before announcing recovery.
