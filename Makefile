# kritva-sdk: make targets. Standard check targets (kritva-program v2/planning/ACCEPTANCE_STANDARD.md).
# Kritva Makefile standard (kritva-program v2/planning/standards/MAKEFILE_STANDARD.md): `make` or `make help` lists the targets.
# A target is documented by `name: ## text` on its rule line; `##@ Name` starts a help group.
# An unimplemented gate exits 3 (NOT_IMPLEMENTED) and an incomplete run exits 4. Neither is a pass.
.DEFAULT_GOAL := help
.PHONY: help

##@ Help
help: ## Show this list
	@awk 'BEGIN { FS = ":.*##"; printf "\nUsage: make <target> [VAR=value ...]\n" } \
	  /^##@/ { g = substr($$0, 5); next } \
	  /^[a-zA-Z0-9_.-]+:[^=].*##/ { if (g != "") { printf "\n%s\n", g; g = "" }; sub(/^ +/, "", $$2); printf "  %-24s %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

##@ Checks
.PHONY: check docs-check check-readme schema-drift

REQUIRED := ACCEPTANCE_CRITERIA.md AGENTS.md CONTRIBUTING.md SECURITY.md LICENSE README.md \
  planning/TASKS.md planning/MILESTONE.md planning/MILESTONE_STATUS.md planning/REVIEW_CHECKLIST.md \
  planning/GIT_COMMIT_STEP.md planning/CHANGELOG.md .github/CODEOWNERS

check: ## Required planning files exist; commit-message checker tests pass
	@for f in $(REQUIRED); do test -f $$f || { echo "missing $$f"; exit 1; }; done
	@python3 -m unittest discover -s tests/commit_message_check
	@echo "check ok"

docs-check: ## Every relative Markdown link points to an existing file (vendored upstream files excluded)
	@python3 scripts/docs_check.py

check-readme: ## Structural check of README.md (metadata, topics, relative links)
	@python3 scripts/check_readme.py README.md

schema-drift: ## Check the vendored Sense contract files and fixtures against their PROVENANCE.json (offline; same as the schema-drift workflow)
	@python3 scripts/check_schema_drift.py

##@ Gates (an incomplete or unimplemented gate never passes: exit 4 or 3)
.PHONY: lint test-unit test-integration test-regression test regression-golden acceptance packaging-test conformance-test oracle-fetch

lint: ## Static checks of the Python files: syntax, unused and wildcard imports, bare except, mutable defaults, whitespace, no print or forbidden import in the library
	@python3 scripts/lint.py
test-unit: ## Unit tests: package, errors, compatibility, config, Sense validator and models, vendored fixtures, drift checker (KOS-SDK-002, KOS-SDK-003)
	@python3 -m unittest discover -s tests/unit
test-integration: ## Integration gate INT-01 to INT-07 (isolated import, wire path, negative path, drift, oracle, packaging, JSON Schema subset); a skipped scenario exits 4 (INCOMPLETE). Needs the oracle (make oracle-fetch), PyPI or KRITVA_WHEELHOUSE, and jsonschema
	@python3 scripts/integration_gate.py --full
test-regression: ## Regression gate REG-01 to REG-07: public API, contract constants, fixture results, error behaviour, config and vendored hashes against tests/regression/golden
	@python3 scripts/regression_gate.py
test: ## All tests: runs test-unit, test-integration and test-regression once each, shows the three results separately and fails if any one fails or is incomplete
	@python3 scripts/test_all.py
regression-golden: ## Show whether the regression golden data are current; WRITE=1 rewrites them (only after the change was decided, tests/regression/README.md)
	@python3 scripts/regression_gate.py $(if $(WRITE),--write,)
acceptance: ## Acceptance gate: runs the automatable criteria of KOS-SDK-001..003 (tests/acceptance/ACCEPTANCE_MAP.json); manual criteria are listed, never passed; a skip exits 4
	@python3 scripts/acceptance_gate.py --full
packaging-test: ## Build the wheel and sdist in a hash-pinned environment and install each in a clean venv (needs PyPI or KRITVA_WHEELHOUSE; KOS-SDK-002)
	@KRITVA_PACKAGING_TESTS=1 python3 -m unittest discover -s tests/packaging -v
oracle-fetch: ## Check out the pinned kritva-sense oracle into .cache/kritva-sense (network; test-only; used by test-integration and acceptance)
	@python3 scripts/oracle_fetch.py
conformance-test: ## Cross-validate against the pinned kritva-sense oracle (set KRITVA_SENSE_ORACLE; KRITVA_REQUIRE_ORACLE=1 makes absence a failure; KOS-SDK-003)
	@python3 -m unittest discover -s tests/conformance -v

##@ Preflight
# "make preflight" is the one command to run before pushing. It runs the checks CI runs on a pull request,
# keeps going after a failure, prints a summary, fixes nothing and never fetches or installs anything.
# Not mirrored: secret-scan (gitleaks), the PR gate's remote rules (required workflows and approvals), and the gates
# that need the network or the pinned kritva-sense checkout (test-integration, acceptance, packaging-test, conformance-test).
# PREFLIGHT_BASE is the branch the commits are compared with; run "git fetch origin" first.
.PHONY: preflight preflight-commits readme-test python-check progress-check hooks-install preflight-hook-on preflight-hook-off

PREFLIGHT_BASE ?= origin/main
PREFLIGHT_STEPS := python-check lint check docs-check check-readme readme-test progress-check schema-drift preflight-commits test-unit test-regression

preflight: ## Run the CI checks locally and report every failure (PREFLIGHT_BASE=origin/main)
	@fail=""; \
	for step in $(PREFLIGHT_STEPS); do \
	  echo ""; echo "[preflight] >>> $$step"; \
	  if $(MAKE) --no-print-directory $$step; then :; else fail="$$fail $$step"; fi; \
	done; \
	echo ""; \
	if [ -n "$$fail" ]; then \
	  echo "[preflight] FAILED:$$fail"; \
	  echo "[preflight] Fix these, then run make preflight again. CI would reject this push."; \
	  exit 1; \
	fi; \
	echo "[preflight] All preflight checks passed. CI also runs secret-scan."

preflight-commits: ## Check the commits since PREFLIGHT_BASE: message rules, commit format and the PR gate (static)
	@git rev-parse --verify --quiet "$(PREFLIGHT_BASE)^{commit}" >/dev/null || { echo "[preflight-commits] $(PREFLIGHT_BASE) not found. Run: git fetch origin"; exit 2; }
	@python3 scripts/security/check_commit_messages.py --range "$(PREFLIGHT_BASE)..HEAD"
	@python3 scripts/security/check_commit_format.py --range "$(PREFLIGHT_BASE)..HEAD"
	@python3 scripts/pipeline/pr_gate.py static --gate .github/kritva-gate.json --base "$(PREFLIGHT_BASE)" --head HEAD

readme-test: ## Run the README checker unit tests (same as the readme-check workflow)
	@python3 -m unittest discover -s tests/readme_check -v

python-check: ## Check python3 is Python 3.12 or newer (the package requires >=3.12; CI uses 3.12 and 3.13)
	@python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 12) else 1)' || { echo "[python-check] python3 is older than 3.12 (the package requires >=3.12). Put Python 3.12 first on PATH, for example: python3.12 -m venv ~/.venvs/kritva312 && . ~/.venvs/kritva312/bin/activate (the pre-push hook uses the same python3)."; exit 1; }

progress-check: ## Check status/STATUS.md against its pinned program snapshot (same as the progress-check workflow)
	@python3 scripts/progress_report.py --check

hooks-install: ## Enable the repository Git hooks (.githooks): make preflight runs before every git push
	git config core.hooksPath .githooks
	@echo "[hooks] core.hooksPath set to .githooks; pre-push runs make preflight."
	@echo "[hooks] Turn it off with: make preflight-hook-off. Skip it once with: git push --no-verify"

preflight-hook-on: ## Run "make preflight" before every git push (the default after hooks-install)
	git config kritva.preflightOnPush true
	@echo "[hooks] pre-push preflight is ON for this clone. It needs core.hooksPath (make hooks-install)."

preflight-hook-off: ## Turn off the pre-push preflight in this clone (CI still runs every check)
	git config kritva.preflightOnPush false
	@echo "[hooks] pre-push preflight is OFF for this clone."

##@ Git
.PHONY: git_sync
git_sync: ## Switch to main, fast-forward from origin, prune, delete merged local branches
	@git switch main
	@git pull --ff-only --prune
	@git branch --format='%(refname:short)' | grep -vx main | xargs -r git branch -d
	@git log --oneline -3
