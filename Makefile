.PHONY: validate test claude-validate live-smoke

validate:
	python3 scripts/validate_repository.py
	python3 -m unittest discover -s tests -v

test: validate

claude-validate:
	claude plugin validate . --strict
	claude plugin validate ./plugins/vucar --strict
	claude plugin tag ./plugins/vucar --dry-run

live-smoke:
	python3 scripts/smoke_test_mcp.py
