# KOS-SDK-002 — Establish Python Package Foundation and Reproducible Build

Status: PROPOSED / PLANNING_ONLY; owner approved the start on 2026-11-25 (implementation in progress, no credit until acceptance). Milestone: V2-M2-SDK-001. Scope aligned 2026-11-24: package foundation only; contract implementation belongs to KOS-SDK-003.

Objective: create an installable, typed Python package with controlled dependencies, supported Python versions, version metadata and reproducible artifacts.

In scope: `src/kritva_sdk/` package layout, `pyproject.toml` with a pinned setuptools build backend, `py.typed`, minimal metadata and version handling, wheel and source-distribution builds, clean virtual-environment install and import tests from both artifacts, Python 3.12 CI (minimum and current supported version).

Out of scope (moved to KOS-SDK-003): vendored schemas, provenance manifest, drift check, contract-version compatibility, configuration and error APIs beyond scaffolding, Sense models and validation. Also out of scope: Mind/Motion models, HTTP client, CLI, job submission, runtime adapters, Control Plane, simulator, public release before gates.

Dependencies: SDK-001 approved; Python 3.12+ and zero runtime dependencies (ADR-001); formal owner start.
