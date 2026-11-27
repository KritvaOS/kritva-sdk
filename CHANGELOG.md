# Changelog

## Unreleased
- Establish proposed Python-first SDK architecture, governance and V2-aligned planning.
- No runtime API, package implementation or release is included.
- KOS-SDK-003 stage a: add `kritva_sdk.errors` (typed errors preserving upstream codes), `kritva_sdk.compat` (`supported_contracts()`, early version checks) and a minimal frozen `SdkConfig`. Planning-only; no release.
- KOS-SDK-003 stage b: vendor the pinned Sense 0.1.0 schema and contract prose (kritva-sense v0.2.0, commit 543f5743d6ffd8fa1ed1ee5fdbf8295ae6a69a77) with PROVENANCE.json, ship them as package data in the wheel and sdist, and add `scripts/check_schema_drift.py`. Planning-only; no release.
- KOS-SDK-003 stage c: add `kritva_sdk.sense` with a hand-written, standard-library, context-free validator (`validate_sample`, `parse_sample`) and frozen typed models (`SenseSample`, `Timestamp`, `Measurement`). Freshness and sequence checks are not included. Planning-only; no release.
- KOS-SDK-003 stage d: vendor the upstream Sense fixtures with provenance, run them offline in the unit tests, and add oracle cross-validation against the pinned kritva-sense validator, generator and conformance harness (`make conformance-test`, CI-enforced). Planning-only; no release.
- Record task dispositions: KOS-SDK-001 to 003 complete with program acceptance pending (owner decision 2026-11-26, interim D-047); KOS-SDK-004 to 009 approved plan scope (D-153), not started. No credit, no release.
- Align the Makefile with the Kritva Makefile standard used by kritva-sense: `make help` (default goal) with grouped targets, `make check` and `make docs-check` implemented, `python-check`, `make preflight` extended, and `make git_sync`. The gates `lint`, `test-integration`, `test-regression`, `test` and `acceptance` still exit 3 (NOT_IMPLEMENTED). `docs-check` skips vendored upstream files.
- Implement the required local gates: `make lint`, `test-integration` (INT-01..07), `test-regression` (REG-01..07 with golden data), `test`, `acceptance` (KOS-SDK-001..003 criteria map) and `oracle-fetch`; add the `gates` workflow. An incomplete gate exits 4. Planning-only; no release.
