# ADR-001 — SDK Language, Package and Visibility

Status: PROPOSED (owner-approved items marked). Local to kritva-sdk; not a central program decision. Revised 2026-11-24.

## Decisions

| Item | Decision | Status |
|---|---|---|
| Repository visibility | PUBLIC | Owner decision, 2026-11-24 |
| CODEOWNER | `@dineshannayya` | Owner confirmed, 2026-11-24 |
| SDK placement | Separate repository `KritvaOS/kritva-sdk` (D-149, supersedes D-144 for the SDK) | Owner decision, 2026-11-24; merged in kritva-program PR 139 |
| First language | Python; C++ bindings and language parity deferred | PROPOSED |
| Python support | 3.11+ with an explicit, bounded supported-version matrix | PROPOSED |
| Distribution name | `kritva-sdk` (replaces the earlier `kritva` proposal) | PROPOSED; PyPI availability not confirmed (a pip lookup found neither name, which is not conclusive) |
| Import namespace | `kritva_sdk`, avoiding a generic top-level `kritva` | PROPOSED |
| First release shape | Contract-first library: typed models and validators for approved contracts; no network client | PROPOSED |
| Model strategy | Hand-written typed models; vendored JSON Schema stays normative; conformance tests tie them together; generated code is not the public API in the first release | PROPOSED |
| Schema handling | Vendored immutable snapshots with provenance (repo, path, version, tag, commit SHA, checksum, approval status) and a CI drift check; no build-time fetch | PROPOSED |
| ROS 2 | Optional extra later; base import must not require it | PROPOSED |
| First release | 0.1.0 preview only after acceptance gates pass | PROPOSED |

## Notes
- The central private decisions D-039/D-063 on visibility class were not readable from this repository. This ADR records the owner's decision and does not cite them as satisfied.
- Hard real-time guarantees are not claimed from Python.
