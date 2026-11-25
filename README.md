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
| Architecture | [ARCHITECTURE.md](ARCHITECTURE.md) (PROPOSED) |
| Milestones | [planning/MILESTONE.md](planning/MILESTONE.md) (PROPOSED) |
| Tasks | [planning/TASKS.md](planning/TASKS.md) (PROPOSED / PLANNING_ONLY) |
| Acceptance Criteria | [ACCEPTANCE_CRITERIA.md](ACCEPTANCE_CRITERIA.md) (PROPOSED) |
| Status Reporting | Pending central SDK workstream registration |
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

The local plan maps to V2-M1, M2, M3, M5, M7 and M8. V2-M4 is not a direct SDK deliverable; V2-M6 remains HOLD and no physical integration work is claimed. The central `SDK` workstream currently has no repository assigned and the central milestone plan has no SDK repository rows. All local tasks therefore remain PROPOSED / PLANNING_ONLY, with no weights or program credit, until central registration and approval.

## Status Reporting and Program Integration

This baseline establishes planning and governance only. No SDK runtime API, package, adapter or release is claimed as implemented.

## Architecture

The SDK is a client-side library. It sits above Skill and approved service APIs and consumes versioned upstream contracts without redefining them. The proposed boundaries and package layout are in [ARCHITECTURE.md](ARCHITECTURE.md); decisions are recorded in [docs/adr/](docs/adr/).

## Toolchain and Development Workflow

Python is the first language (3.12+ proposed, see [ADR-001](docs/adr/ADR-001-sdk-language-and-package.md)). No package build exists yet. `make hooks-install` enables the pre-push hook, and `make preflight` runs the CI checks that are implemented. Engineering gates (`make check`, `make test`) report NOT_IMPLEMENTED and exit non-zero; that is not a pass.

## Dependencies and Interfaces

Upstream contracts and their approval state are tracked in [planning/dependencies/CONTRACT_DEPENDENCY_REGISTER.md](planning/dependencies/CONTRACT_DEPENDENCY_REGISTER.md). A draft contract is never pinned as an approved dependency.

## Tasks and Acceptance Criteria

Tasks are listed in [planning/TASKS.md](planning/TASKS.md). Each has a TASK.md and ACCEPTANCE_CRITERIA.md under `planning/milestones/`. Repository-level criteria are in [ACCEPTANCE_CRITERIA.md](ACCEPTANCE_CRITERIA.md).

## Build, Test, Regression and Validation

No tests of SDK behavior exist yet. The strategy is in [TESTING.md](TESTING.md). Only the README and commit-message checks run today. Simulation evidence is never physical or safety validation.

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
