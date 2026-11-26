# Kritva SDK

> Python-first developer SDK for applications built on the Kritva Open Robotic Computing Platform.

| Property | Value |
|---|---|
| Project | KritvaOS |
| Repository | `KritvaOS/kritva-sdk` |
| Repository Type | Library |
| Visibility Class | PUBLIC (owner decision, 2026-11-24; recorded in [ADR-001](docs/adr/ADR-001-sdk-language-and-package.md)) |
| GitHub Setting | PUBLIC (observed 2026-11-24) |
| Lifecycle Status | PLANNING |
| Repository Owner | Project owner |
| Architecture | [ARCHITECTURE.md](ARCHITECTURE.md) (design approved by the owner, D-150) |
| Milestones | [planning/MILESTONE.md](planning/MILESTONE.md) (local mapping; none closed) |
| Tasks | [planning/TASKS.md](planning/TASKS.md) (001 to 003 complete, acceptance pending; 004 to 009 approved plan, not started) |
| Acceptance Criteria | [ACCEPTANCE_CRITERIA.md](ACCEPTANCE_CRITERIA.md) (PROPOSED) |
| Status Reporting | [status/status.json](status/status.json) (schema 2.0) and the generated progress view [status/STATUS.md](status/STATUS.md) (see Status Reporting and Program Integration) |
| License | [LICENSE](LICENSE) (Apache-2.0) |

## Purpose and Scope

Kritva SDK provides a consistent Python developer interface over approved Kritva component contracts and service APIs. It owns client ergonomics, typed interfaces, configuration, transport adapters, compatibility declarations, packaging, examples and documentation. It does not redefine upstream contracts or take ownership of runtime, Control Plane, simulation, hardware or safety behavior.

## Position in the KritvaOS Ecosystem

```text
Applications
    |
Kritva SDK
    |
Skill / approved service APIs
    |
Mind / Motion / Sense capability contracts
    |
Kritva Core contracts
    |
Runtime / platform / hardware integrations
```

## Documents to Read First

1. [AGENTS.md](AGENTS.md) — contributor and agent rules
2. [ARCHITECTURE.md](ARCHITECTURE.md) — ownership and architecture
3. [REQUIREMENTS.md](REQUIREMENTS.md) — requirements
4. [API.md](API.md) — proposed public API
5. [TESTING.md](TESTING.md) — test strategy
6. [ACCEPTANCE_CRITERIA.md](ACCEPTANCE_CRITERIA.md) — repository acceptance
7. [planning/README.md](planning/README.md) — planning control
8. [planning/MILESTONE.md](planning/MILESTONE.md) and [planning/TASKS.md](planning/TASKS.md) — V2 alignment

## Repository Structure and File Responsibilities

- `src/kritva_sdk/`: Python package source (SDK-002); `pyproject.toml` and `release/` hold metadata and the pinned build.
- `tests/`: unit, contract, integration and regression tests.
- `examples/`: executable developer examples.
- `docs/`: API and developer guides.
- `schemas/`: SDK-owned schemas only; upstream contracts remain authoritative upstream.
- `planning/`: milestone, task and review records.

No empty source folders or placeholder modules are created before their first deliverable. The target package layout is documented in [ARCHITECTURE.md](ARCHITECTURE.md).

## Milestones and Implementation Plan

The local plan maps to V2-M1, M2, M3, M5, M7 and M8. V2-M4 is not a direct SDK deliverable; V2-M6 remains HOLD and no physical integration work is claimed. The central program registers this repository as the `SDK` workstream (kritva-program D-149), with planning rows and weights in the approved plan register (D-153). KOS-SDK-001 to 003 are complete in this repository and the owner decided on 2026-11-26 to accept them (interim D-047 review, not independent); KOS-SDK-004 to 009 are approved plan scope (D-153), not started. None is in the frozen program baseline yet, and nothing here earns program credit until kritva-program baselines, approves and records a task.

## Status Reporting and Program Integration

**Progress view.** [status/STATUS.md](status/STATUS.md) is a generated progress view: a bar of accepted weight, with the program's milestone breakdown. `scripts/progress_report.py` renders it from the pinned snapshot `status/program_snapshot.json`, which kritva-program writes (`tools/publish_repo_progress.py`, decision D-120). The `progress-check` workflow runs on pull requests and on pushes to main, runs `python3 scripts/progress_report.py --check` (read-only), and fails when the report and the snapshot differ. The view is a derived snapshot and can lag the program; the record is the [program status view](https://github.com/KritvaOS/kritva-program/blob/main/v2/tracking/STATUS_VIEW.md).

**Status report.** [status/status.json](status/status.json) (schema 2.0, [status/README.md](status/README.md)) reports facts only. Its `tasks` list is empty because no SDK task is baselined: KOS-SDK-001 to KOS-SDK-009 are in [planning/TASKS.md](planning/TASKS.md), carry no weight in the baseline and earn no program credit; status.json will list KOS-SDK-001 to 003 only after kritva-program baselines them. kritva-program decides baseline, weights, approvals and gates.

**Implementation maturity is separate from program acceptance.** The package foundation (KOS-SDK-002: `src/kritva_sdk/`, `pyproject.toml`, the pinned reproducible build and the unit and packaging tests) is implemented and merged. It is planning-only, not baselined and not accepted. KOS-SDK-003 is implemented in four merged stages and is likewise planning-only, not baselined and not accepted: typed errors, contract compatibility, a minimal configuration, the vendored Sense 0.1.0 contract files and a hand-written, context-free Sense sample validator with typed models exist, with upstream fixtures and oracle cross-validation. The SDK has no network client, CLI or release yet; freshness and sequence checks are not implemented; no runtime API, adapter or release is claimed as stable or accepted.

| Dimension | Source record | Authority |
|---|---|---|
| Execution | the task status in [planning/TASKS.md](planning/TASKS.md); 001 to 003 complete (acceptance pending), 004 to 009 approved plan, not started | The task owner records it |
| Evidence | none recorded in the status source: SDK-002 implementation is in the merged pull request history, not cited as task evidence | Evidence is recorded at acceptance, by the author, and checked by another reviewer |
| Acceptance | [ACCEPTANCE_CRITERIA.md](ACCEPTANCE_CRITERIA.md), the review record and the central approvals in kritva-program | The independent reviewer and the owner, never a status report |
| Release readiness | not defined: no release, tag or completion record exists | The owner, through the central gates |

## Architecture

The SDK is a client-side library. It sits above Skill and approved service APIs and consumes versioned upstream contracts without redefining them. The proposed boundaries and package layout are in [ARCHITECTURE.md](ARCHITECTURE.md); decisions are recorded in [docs/adr/](docs/adr/).

## Toolchain and Development Workflow

Python is the first language (3.12+ proposed, see [ADR-001](docs/adr/ADR-001-sdk-language-and-package.md)). No package build exists yet. `make hooks-install` enables the pre-push hook, and `make preflight` runs the CI checks that are implemented. Engineering gates (`make check`, `make test`) report NOT_IMPLEMENTED and exit non-zero; that is not a pass.

## Dependencies and Interfaces

Upstream contracts and their approval state are tracked in [planning/dependencies/CONTRACT_DEPENDENCY_REGISTER.md](planning/dependencies/CONTRACT_DEPENDENCY_REGISTER.md). A draft contract is never pinned as an approved dependency.

## Tasks and Acceptance Criteria

Tasks are listed in [planning/TASKS.md](planning/TASKS.md). Each has a TASK.md and ACCEPTANCE_CRITERIA.md under `planning/milestones/`. Repository-level criteria are in [ACCEPTANCE_CRITERIA.md](ACCEPTANCE_CRITERIA.md).

## Build, Test, Regression and Validation

The strategy is in [TESTING.md](TESTING.md). Today `make test-unit` runs the package unit tests, `make packaging-test` builds the wheel and source distribution in a hash-pinned environment and installs each into a clean virtual environment, and the README, commit-message, progress and vendored-schema drift checks run (`make preflight`; `make schema-drift` verifies the pinned Sense files against `src/kritva_sdk/_schemas/sense/PROVENANCE.json`). The engineering gates `check`, `lint`, `docs-check`, `test-integration`, `test-regression` and `acceptance` are still NOT_IMPLEMENTED. Unit tests of the Sense models and validator exist, and `make conformance-test` cross-validates them against the pinned kritva-sense reference implementation, used as a test-only oracle (see [TESTING.md](TESTING.md)). Simulation evidence is never physical or safety validation.

## Git Workflow and Review

Work on branches and open pull requests; do not push to `main`. Follow [CONTRIBUTING.md](CONTRIBUTING.md) and the commit rules in [AGENTS.md](AGENTS.md).

## Safety and Security

See [SECURITY.md](SECURITY.md). Client-side validation never replaces server authorization or safety checks. Never commit credentials or personal data.

## Release and Versioning

No release exists. A 0.1.0 preview is planned only after the acceptance gates pass. See [CHANGELOG.md](CHANGELOG.md).

## Ownership and Escalation

The project owner (`@dineshannayya`, see [.github/CODEOWNERS](.github/CODEOWNERS)) decides architecture, scope and releases. Upstream contract questions go to the owning repository.

## Related Repositories and References

`kritva-core`, `kritva-sense`, `kritva-skill` and `kritva-program` (central decisions and status) under the KritvaOS organization.

## License

Apache-2.0. See [LICENSE](LICENSE).
