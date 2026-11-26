# KOS-SDK-002 — Establish Python Package Foundation and Reproducible Build

Status: COMPLETE in this repository; owner decision to accept 2026-11-26 (interim D-047, not independent); program acceptance, baseline and approval record pending; no credit. Milestone: V2-M2-SDK-001. Scope aligned 2026-11-24: package foundation only; contract implementation belongs to KOS-SDK-003.

Objective: create an installable, typed Python package with controlled dependencies, supported Python versions, version metadata and reproducible artifacts.

In scope: `src/kritva_sdk/` package layout, `pyproject.toml` with a pinned setuptools build backend, `py.typed`, minimal metadata and version handling, wheel and source-distribution builds, clean virtual-environment install and import tests from both artifacts, Python 3.12 CI (minimum and current supported version).

Out of scope (moved to KOS-SDK-003): vendored schemas, provenance manifest, drift check, contract-version compatibility, configuration and error APIs beyond scaffolding, Sense models and validation. Also out of scope: Mind/Motion models, HTTP client, CLI, job submission, runtime adapters, Control Plane, simulator, public release before gates.

Dependencies: SDK-001 approved; Python 3.12+ and zero runtime dependencies (ADR-001); formal owner start.
