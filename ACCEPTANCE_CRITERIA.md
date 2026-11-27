# Acceptance Criteria: kritva-sdk

Standard: Kritva V2 acceptance standard in kritva-program (PD-005 / PD-006; canonical copy maintained in kritva-standard). These repository-level criteria are PROPOSED. Task criteria live beside each task under `planning/milestones/`.

## 1. Purpose and scope
Owns Python developer APIs, client ergonomics, typed models, configuration, transport adapters, compatibility declarations, packaging, examples and docs. Does not own upstream contracts, Control Plane service, simulator, hardware drivers, safety policy or physical validation.

## 2. Normative dependencies
Consume approved versioned contracts from kritva-core, -sense, -motion, -mind, -skill and approved Control Plane/simulation APIs. Pin exact versions or commits before implementing each adapter. No upstream version is pinned by this planning baseline.

## 3. Functional criteria
| ID | Criterion | Verified by |
|---|---|---|
| SDK-AC-001 | Base package imports without ROS 2, simulator or hardware dependencies. | clean import test |
| SDK-AC-002 | Public APIs are typed and documented. | API review/type checks |
| SDK-AC-003 | Adapters declare supported upstream contract versions. | compatibility tests |
| SDK-AC-004 | Timeout, cancellation, retries and idempotency are explicit and tested. | unit/integration tests |
| SDK-AC-005 | Secrets are not logged or exposed in exception text. | security tests |
| SDK-AC-006 | Examples run against mocks/simulation and label evidence correctly. | smoke tests |
| SDK-AC-007 | No SDK validation is described as physical or safety validation. | docs review |
| SDK-AC-008 | Build artifacts are versioned, reproducible and integrity checked. | build/release checks |

## 4. Compatibility
SDK SemVer and upstream contract versions are independent. Breaking SDK changes require MAJOR version, migration notes and regression evidence. No ABI or hard real-time guarantee applies to Python.

## 5. Test gates
| Gate | Command | State |
|---|---|---|
| Structure | make check | IMPLEMENTED (see TESTING.md) |
| Lint | make lint | IMPLEMENTED (see TESTING.md) |
| Unit | make test-unit | IMPLEMENTED (see TESTING.md) |
| Integration | make test-integration | IMPLEMENTED (see TESTING.md) |
| Regression | make test-regression | IMPLEMENTED (see TESTING.md) |
| Combined | make test | IMPLEMENTED (see TESTING.md) |
| Docs | make docs-check | IMPLEMENTED (see TESTING.md) |
| Acceptance | make acceptance | IMPLEMENTED (see TESTING.md) |

No coverage threshold is set. An unimplemented gate is not a pass.

## 6. Specialised gates
Contract compatibility, deterministic errors, timeout/cancellation, dependency isolation and secret handling apply. Physical validation remains outside SDK scope; V2-M6 HOLD is not bypassed.

## 7. Evidence
Immutable commit SHAs, CI run IDs, test reports, dependency audit, compatibility matrix and review records. Simulation is explicitly labelled.

## 8. Definition of done
Follow Kritva V2 standard: stable task ID, approved criteria, merged PR, required checks on exact commit, recorded reviews, docs/changelog, immutable evidence and no blocker converted into pass.

## 9. Known limitations
SDK repository is not yet assigned in the central SDK workstream. KOS-SDK-001 to 003 are complete with program acceptance pending and KOS-SDK-004 to 009 are approved plan scope (D-153); none has weight or credit until kritva-program baselines it. Upstream versions and Control Plane API remain unpinned. No runtime or passing gate is claimed.

## 10. Change control
Accepted criteria are immutable. Changes require a new revision and review.
