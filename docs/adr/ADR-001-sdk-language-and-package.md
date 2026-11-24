# ADR-001 — SDK Language, Package and Visibility

Status: PROPOSED (owner-approved items marked). Local to kritva-sdk; not a central program decision.

## Decisions

| Item | Decision | Status |
|---|---|---|
| Repository visibility | PUBLIC | Owner decision, 2026-11-24 |
| CODEOWNER | `@dineshannayya` | Owner confirmed, 2026-11-24 |
| First language | Python; C++ bindings and language parity deferred | PROPOSED |
| Python support | 3.11+ with an explicit, bounded supported-version matrix | PROPOSED |
| Distribution name | `kritva` (PyPI-compatible) | PROPOSED; availability not yet verified |
| Import namespace | To be chosen and checked separately from the distribution name | OPEN |
| ROS 2 | Optional extra; base import must not require it | PROPOSED |
| First release | 0.1.0 preview only after acceptance gates pass | PROPOSED |

## Notes
- The central private decisions D-039/D-063 on visibility class were not readable from this repository. This ADR records the owner's decision and does not cite them as satisfied.
- Name availability on PyPI must be checked before SDK-002 relies on it.
- Hard real-time guarantees are not claimed from Python.
