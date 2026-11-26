# Changelog

## Unreleased
- Establish proposed Python-first SDK architecture, governance and V2-aligned planning.
- No runtime API, package implementation or release is included.
- KOS-SDK-003 stage a: add `kritva_sdk.errors` (typed errors preserving upstream codes), `kritva_sdk.compat` (`supported_contracts()`, early version checks) and a minimal frozen `SdkConfig`. Planning-only; no release.
- KOS-SDK-003 stage b: vendor the pinned Sense 0.1.0 schema and contract prose (kritva-sense v0.2.0, commit 543f5743d6ffd8fa1ed1ee5fdbf8295ae6a69a77) with PROVENANCE.json, ship them as package data in the wheel and sdist, and add `scripts/check_schema_drift.py`. Planning-only; no release.
- KOS-SDK-003 stage c: add `kritva_sdk.sense` with a hand-written, standard-library, context-free validator (`validate_sample`, `parse_sample`) and frozen typed models (`SenseSample`, `Timestamp`, `Measurement`). Freshness and sequence checks are not included. Planning-only; no release.
