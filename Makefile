# Kritva V2 required gates. Until implemented, gates fail explicitly (NOT_IMPLEMENTED).
.PHONY: check lint test-integration test-regression test docs-check acceptance test-unit packaging-test

check lint test-integration test-regression test docs-check acceptance:
	@echo "NOT_IMPLEMENTED: $@"
	@exit 3

# "make preflight" runs the CI checks that exist today before a push. It keeps going after a failure and fixes nothing.
# Engineering gates (check, test-*, docs-check, acceptance) stay NOT_IMPLEMENTED and are deliberately not part of preflight.
# Not mirrored: secret-scan (gitleaks) and the PR gate's remote rules. PREFLIGHT_BASE is compared with HEAD; run "git fetch origin" first.
.PHONY: preflight preflight-commits check-readme readme-test progress-check schema-drift hooks-install preflight-hook-on preflight-hook-off

PREFLIGHT_BASE ?= origin/main
PREFLIGHT_STEPS := check-readme readme-test progress-check schema-drift preflight-commits

check-readme:
	@python3 scripts/check_readme.py README.md

readme-test:
	@python3 -m unittest discover -s tests/readme_check -v

progress-check: ## Check status/STATUS.md against its pinned program snapshot (same as the progress-check workflow)
	@python3 scripts/progress_report.py --check

schema-drift: ## Check the vendored Sense contract files against PROVENANCE.json (offline; same as the schema-drift workflow)
	@python3 scripts/check_schema_drift.py

preflight:
	@fail=""; \
	for step in $(PREFLIGHT_STEPS); do \
	  echo ""; echo "[preflight] >>> $$step"; \
	  if $(MAKE) --no-print-directory $$step; then :; else fail="$$fail $$step"; fi; \
	done; \
	echo ""; \
	if [ -n "$$fail" ]; then echo "[preflight] FAILED:$$fail"; exit 1; fi; \
	echo "[preflight] All preflight checks passed. CI also runs secret-scan."

preflight-commits:
	@git rev-parse --verify --quiet "$(PREFLIGHT_BASE)^{commit}" >/dev/null || { echo "[preflight-commits] $(PREFLIGHT_BASE) not found. Run: git fetch origin"; exit 2; }
	@python3 scripts/security/check_commit_messages.py --range "$(PREFLIGHT_BASE)..HEAD"
	@python3 scripts/security/check_commit_format.py --range "$(PREFLIGHT_BASE)..HEAD"
	@python3 scripts/pipeline/pr_gate.py static --gate .github/kritva-gate.json --base "$(PREFLIGHT_BASE)" --head HEAD

hooks-install:
	git config core.hooksPath .githooks
	@echo "[hooks] core.hooksPath set to .githooks; pre-push runs make preflight."

preflight-hook-on:
	git config kritva.preflightOnPush true

preflight-hook-off:
	git config kritva.preflightOnPush false

# KOS-SDK-002: unit tests need only the standard library. packaging-test builds in a hash-pinned environment and needs
# network access to PyPI or a wheelhouse (KRITVA_WHEELHOUSE).
test-unit:
	python3 -m unittest discover -s tests/unit -v

packaging-test:
	KRITVA_PACKAGING_TESTS=1 python3 -m unittest discover -s tests/packaging -v
