# Kritva SDK Requirements

**Status:** APPROVED baseline for the SDK (SDK-001, D-150; interim D-047, not independent). Requirements for KOS-SDK-004 to 009 stay conditional on their upstream contracts.

## Functional
| ID | Requirement | Verification |
|---|---|---|
| SDK-F-001 | Provide a documented Python package and stable import namespace. | package/import tests |
| SDK-F-002 | Provide explicit, immutable configuration; client lifecycle applies only once a network client exists. | unit tests |
| SDK-F-003 | Expose typed, version-aware interfaces for approved Kritva APIs. | contract tests |
| SDK-F-004 | Map upstream errors without losing source codes/context. | error tests |
| SDK-F-005 | Define bounded timeout and cancellation behavior for async operations. | async tests |
| SDK-F-006 | Keep ROS 2 and simulator dependencies optional. | clean-install tests |
| SDK-F-007 | Provide executable examples against mocks or supported simulation. | example smoke tests |
| SDK-F-008 | Expose telemetry/results only where upstream contracts define them. | contract tests |

## Non-functional
| ID | Requirement | Verification |
|---|---|---|
| SDK-NF-001 | Minimize and document base dependencies. | dependency audit |
| SDK-NF-002 | Public APIs are typed and documented. | static checks/review |
| SDK-NF-003 | Unit/contract tests run without physical hardware. | CI |
| SDK-NF-004 | Secrets are not emitted in logs or exception text. | security tests |
| SDK-NF-005 | Upstream compatibility is explicit. | compatibility matrix |
| SDK-NF-006 | Errors, timeout and cleanup behavior are deterministic. | contract/regression tests |
| SDK-NF-007 | No unsupported real-time, physical or safety claims. | review |

## Exclusions
Motor control, FOC, EtherCAT, firmware, sensor drivers, canonical component schemas, motion planning, Mind inference, Skill orchestration, Control Plane server, simulator implementation, mandatory ROS 2 and C++ SDK in the first implementation phase.

Accepted requirements are versioned; do not rewrite accepted criteria or evidence.
