# ADR-001 — SDK Language, Package and Visibility

Status: PROPOSED (owner-approved items marked). Local to kritva-sdk; not a central program decision. Revised 2026-11-24.

## Decisions

| Item | Decision | Status |
|---|---|---|
| Repository visibility | PUBLIC | Owner decision, 2026-11-24 |
| CODEOWNER | `@dineshannayya` | Owner confirmed, 2026-11-24 |
| SDK placement | Separate repository `KritvaOS/kritva-sdk` (D-149, supersedes D-144 for the SDK) | Owner decision, 2026-11-24; merged in kritva-program PR 139 |
| First language | Python; C++ bindings and language parity deferred | PROPOSED |
| Python support | 3.12+ (replaces 3.11+: Sense and Mind require 3.12 and all sibling CI uses 3.12); CI tests the minimum and the current supported version | PROPOSED |
| Distribution name | `kritva-sdk` (replaces the earlier `kritva` proposal). PyPI normalizes `-`, `_` and `.`, so `kritva-sdk` and `kritva_sdk` are the same distribution name; `kritva_sdk` is the import package | PROPOSED; PyPI availability not confirmed (see Open check) |
| Import namespace | `kritva_sdk`, avoiding a generic top-level `kritva` | PROPOSED |
| First release shape | Contract-first library: typed models and validators for approved contracts; no network client | PROPOSED |
| Model strategy | Hand-written typed models; vendored JSON Schema stays normative; conformance tests tie them together; generated code is not the public API in the first release | PROPOSED |
| Schema handling | Vendored immutable snapshots with provenance (repo, path, version, tag, commit SHA, checksum, approval status) and a CI drift check; no build-time fetch | PROPOSED |
| Runtime dependencies | None in the first release (standard library only). `jsonschema` may be a test-only dependency. Build tooling is pinned; the user's runtime environment is not | PROPOSED |
| Validation | The SDK carries its own validation against its vendored schema. The pinned kritva-sense validator, generator and conformance harness are test/CI oracles only, with cross-validation tests; upstream is authoritative for contract semantics | PROPOSED |
| ROS 2 | Optional extra later; base import must not require it | PROPOSED |
| First release | 0.1.0 preview only after acceptance gates pass | PROPOSED |

## Notes
- The central private decisions D-039/D-063 on visibility class were not readable from this repository. This ADR records the owner's decision and does not cite them as satisfied.
- Hard real-time guarantees are not claimed from Python.

## Name check
The owner checked PyPI on 2026-11-25: `pip index versions kritva-sdk` reported no matching distribution, and both `https://pypi.org/simple/kritva-sdk/` and `https://pypi.org/pypi/kritva-sdk/json` returned 404. The name `kritva-sdk` (the same distribution as `kritva_sdk`) is therefore not currently listed on PyPI. This does not reserve it: the name is confirmed only when PyPI accepts an upload, and a name can be taken at any time before the first release. Re-check before the first release; no upload is planned until the acceptance gates pass and the owner approves a release.
