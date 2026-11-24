# Kritva V2 required gates. Until implemented, gates fail explicitly (NOT_IMPLEMENTED).
.PHONY: check lint test-unit test-integration test-regression test docs-check acceptance

check lint test-unit test-integration test-regression test docs-check acceptance:
	@echo "NOT_IMPLEMENTED: $@"
	@exit 3
