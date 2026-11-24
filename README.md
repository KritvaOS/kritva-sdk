# Kritva SDK

> Python-first developer SDK for applications built on the Kritva Open Robotic Computing Platform.

| Property | Value |
|---|---|
| Project | KritvaOS |
| Repository | `KritvaOS/kritva-sdk` |
| Repository Type | Library |
| Visibility Class | Not yet decided; owner confirmation required |
| GitHub Setting | PUBLIC (observed 2026-11-24) |
| Lifecycle Status | PLANNING |
| Repository Owner | Project owner |
| Architecture | [ARCHITECTURE.md](ARCHITECTURE.md) (PROPOSED) |
| Milestones | [planning/MILESTONE.md](planning/MILESTONE.md) (PROPOSED) |
| Tasks | [planning/TASKS.md](planning/TASKS.md) (PROPOSED / PLANNING_ONLY) |
| Acceptance Criteria | [ACCEPTANCE_CRITERIA.md](ACCEPTANCE_CRITERIA.md) (PROPOSED) |
| Status Reporting | Pending central SDK workstream registration |
| License | [LICENSE](LICENSE) (Apache-2.0) |

## Purpose

Kritva SDK provides a consistent Python developer interface over approved Kritva component contracts and service APIs. It owns client ergonomics, typed interfaces, configuration, transport adapters, compatibility declarations, packaging, examples and documentation. It does not redefine upstream contracts or take ownership of runtime, Control Plane, simulation, hardware or safety behavior.

## Position in KritvaOS

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

## Read first

1. [AGENTS.md](AGENTS.md) — contributor and agent rules
2. [ARCHITECTURE.md](ARCHITECTURE.md) — ownership and architecture
3. [REQUIREMENTS.md](REQUIREMENTS.md) — requirements
4. [API.md](API.md) — proposed public API
5. [TESTING.md](TESTING.md) — test strategy
6. [ACCEPTANCE_CRITERIA.md](ACCEPTANCE_CRITERIA.md) — repository acceptance
7. [planning/README.md](planning/README.md) — planning control
8. [planning/MILESTONE.md](planning/MILESTONE.md) and [planning/TASKS.md](planning/TASKS.md) — V2 alignment

## Repository structure

- `sdk/python/`: Python package source, introduced with SDK-002.
- `tests/`: unit, contract, integration and regression tests.
- `examples/`: executable developer examples.
- `docs/`: API and developer guides.
- `schemas/`: SDK-owned schemas only; upstream contracts remain authoritative upstream.
- `planning/`: milestone, task and review records.

No empty source folders or placeholder modules are created before their first deliverable. The target package layout is documented in [ARCHITECTURE.md](ARCHITECTURE.md).

## Program alignment

The local plan maps to V2-M1, M2, M3, M5, M7 and M8. V2-M4 is not a direct SDK deliverable; V2-M6 remains HOLD and no physical integration work is claimed. The central `SDK` workstream currently has no repository assigned and the central milestone plan has no SDK repository rows. All local tasks therefore remain PROPOSED / PLANNING_ONLY, with no weights or program credit, until central registration and approval.

## Implementation status

This baseline establishes planning and governance only. No SDK runtime API, package, adapter or release is claimed as implemented.
