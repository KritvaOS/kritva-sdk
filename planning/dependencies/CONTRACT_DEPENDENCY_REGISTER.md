# Contract Dependency Register

Status: PROPOSED / PLANNING_ONLY. Initial inventory from the review of 2026-11-24; the Commit SHA column must be filled from the upstream repositories before any dependency is pinned. A DRAFT, PROPOSED or NOT_AVAILABLE contract is never pinned as APPROVED.

| Repository | Contract source | Version | Immutable commit SHA | Status | SDK consumer API | Compatibility constraint | Outstanding upstream dependency |
|---|---|---|---|---|---|---|---|
| kritva-core | `API.md`, `ARCHITECTURE.md` | R1.0 | to be recorded | APPROVED (released) | Core client | to be defined in SDK-001 | none known |
| kritva-sense | `contract/SENSE_CONTRACT.md`, `contract/sense-sample.schema.json` | 0.1.0 | to be recorded | APPROVED | Sense adapter (SDK-005) | pin exact version | none known |
| kritva-motion | `contract/MOTION_CONTRACT.md` | draft | n/a | DRAFT | Motion adapter (SDK-009) | do not pin | approval and tag |
| kritva-mind | `contract/` schemas, `contract/README.md` | draft | n/a | DRAFT | Mind adapter (SDK-009) | do not pin | acceptance |
| kritva-skill | `docs/design/MIND_SKILL_INTERFACE.md` | proposed | n/a | PROPOSED | Skill adapter (SDK-009) | do not pin | approval |
| Sim | none confirmed | n/a | n/a | NOT_AVAILABLE | simulation adapter (SDK-006) | n/a | repository and contract |
| Control Plane | no approved service API | n/a | n/a | NOT_AVAILABLE | Control Plane client (SDK-004) | n/a | approved API and security boundary |

Program documents `v2/architecture/SDK_CONTRACTS.md` and the per-component contract documents do not exist in kritva-program; they must not be cited. `v2/PRS.md` and `v2/REQUIREMENT_TRACEABILITY.md` are skeletons, not approved SDK requirements.

Statuses above come from the 2026-11-24 review and have not been re-verified against each upstream repository.
