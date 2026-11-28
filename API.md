# Kritva SDK Public API Design

**Status:** SDK-001 design approved by the owner (D-150; interim D-047, not independent). The configuration, error, compatibility and Sense (`kritva_sdk.sense`) APIs below are implemented by KOS-SDK-003 in a preview, pre-1.0 form and are not stable; everything else is a candidate only.

## Scope of the first release

The first SDK release is a **contract-first Python library**: typed models and validators over approved, versioned upstream contract schemas. It is not a network client.

- Eligible contracts today, all from kritva-sense at pin tag `v0.2.0` (commit `543f5743d6ffd8fa1ed1ee5fdbf8295ae6a69a77`): the **Sense sample contract 0.1.0**, the **stream contract 0.1.0** and the **frame-graph contract 0.1.0** (all APPROVED). Approval makes a contract eligible, not implemented.
- Staging: the sample contract is implemented (KOS-SDK-003) and the stream and frame-graph contracts are implemented under KOS-SDK-005 (`kritva_sdk.stream`, `kritva_sdk.frame_graph`), each with its own conformance tests. Each contract is pinned by the same tag and commit and declared in `supported_contracts()` only when it is implemented.
- Explicitly excluded until their contracts are approved and versioned: Mind, Motion, Skill, Sim, Control Plane.
- Explicitly excluded: any Core client (Core R1.0 is an in-process C++ API with no Python or network surface), any HTTP or other network implementation, any ROS 2 or simulator adapter.

Distribution name `kritva-sdk`, import namespace `kritva_sdk` (ADR-001). On 2026-11-25 the name was not listed on PyPI (it is confirmed only when PyPI accepts an upload; ADR-001).

## Candidate public surface (illustrative, not stable)

```python
from kritva_sdk import SdkConfig, supported_contracts
from kritva_sdk.sense import SenseSample, validate_sample, parse_sample
from kritva_sdk.stream import StreamChecker, check_stream, parse_stream
from kritva_sdk.frame_graph import parse_frame_graph, resolve, validate_graph
from kritva_sdk.errors import ContractError, UnsupportedContractVersion

supported_contracts()            # {"sense": ("0.1.0",), "stream": ("0.1.0",), "frame_graph": ("0.1.0",)}
sample = parse_sample(payload)   # raises ContractError subclasses with upstream error codes
validate_sample(payload)         # schema validation without building a model
result = check_stream(document)  # StreamResult: STREAM_ diagnostics and sample violations, kept apart
stream = parse_stream(document)  # a conformant Stream, or StreamContractError / UnsupportedStreamVersion
graph = parse_frame_graph(document)         # a conformant FrameGraph, or FrameGraphContractError
resolution = resolve(graph, "sensor", "world")   # Resolution: a canonical transform or the FG_ violations, never both
```

| Area | Responsibility | Authority |
|---|---|---|
| `kritva_sdk.config` | Explicit, validated, immutable configuration | SDK |
| `kritva_sdk.errors` | Typed errors that preserve upstream codes (for example `UNSUPPORTED_CONTRACT_VERSION`, `UNKNOWN_FIELD`, `INVALID_SENSOR_ID`, `INVALID_TIMESTAMP`) | SDK, codes from the contract |
| `kritva_sdk.compat` | Supported-contract declarations and version checks that fail before any operation | SDK |
| `kritva_sdk.sense` | Typed sample models, parse and validate, serialization | kritva-sense (normative schema), SDK (Python surface) |
| `kritva_sdk.stream` | Typed stream models, an incremental checker with `STREAM_` diagnostics, parse and serialization | kritva-sense (normative contract), SDK (Python surface) |
| `kritva_sdk.frame_graph` | Typed transform and graph models, `FG_` validation, deterministic resolution (`resolve`, `transform_point`) | kritva-sense (normative contract), SDK (Python surface) |

### Support matrix (KOS-SDK-005)

| Contract | Version | Status in this SDK | Module |
|---|---|---|---|
| Sense sample | 0.1.0 | implemented (KOS-SDK-003) | `kritva_sdk.sense` |
| Sense stream | 0.1.0 | implemented (KOS-SDK-005); declared in `supported_contracts()` | `kritva_sdk.stream` |
| Sense frame graph | 0.1.0 | implemented (KOS-SDK-005); declared in `supported_contracts()`; synthetic data only | `kritva_sdk.frame_graph` |
| Any other contract or version | any | unsupported: an unsupported version is reported with the upstream code (`STREAM_UNSUPPORTED_VERSION`, `FG_UNSUPPORTED_VERSION`) and is never accepted silently | none |

Stream results say only that records are well formed and consistent under the contract; a conformant frame graph says only that its records are well formed and form a forest, not that a frame, mounting transform or calibration is physically correct. A resolved transform follows the contract convention: pose of the child in the parent, Hamilton unit quaternion `{w, x, y, z}`, metres, canonical sign. They do not establish sensor freshness, calibration, clock synchronisation, physical correctness or safety, and the SDK defines no transport, buffering, loss recovery or stream merging.

Models are hand-written and typed. The vendored JSON Schema stays normative; conformance tests prove that model serialization and validation agree with it. Generated code is not the public API in the first release.

## Behavior rules

- Units, timestamps (`clock`, `unit`, `value`), frame identifiers, `validity` and `error_code` semantics are preserved exactly as the contract defines them; no conversion is hidden.
- Unknown fields are rejected, as the contract requires. Unsupported contract versions fail clearly and early.
- `validate_sample(payload)` returns a tuple of `Violation(path, code, message)` sorted by (path, code, message); an empty tuple means structural conformance only. It never raises for malformed input. `parse_sample(payload)` returns a frozen `SenseSample` or raises `ContractError` (all violations) and, for an unsupported `contract_version` string, `UnsupportedContractVersion` before any other validation is attempted.
- Freshness (`STALE_DATA` from age, clock mismatch, future samples), sequence continuity (`SEQUENCE_REGRESSION`) and the consumer usability decision need the consumer's context (contract section 6.1) and are not implemented by this SDK release. A conformant sample is not thereby fresh, in order or usable.
- `MISSING` samples carry empty measurements; `STALE` and `INVALID` samples keep the last known measurements for diagnosis, and they are not readings. `error_code` is `None` on the model exactly when the field is absent on the wire.
- Validation is synchronous and pure (no I/O); it is safe to call from async code. No timeout or cancellation semantics are needed until a network surface exists.
- The base import has no dependency on ROS 2, a simulator, hardware or a network library.
- Client-side validation never replaces server-side authorization or safety checks. Nothing here makes a real-time or physical-safety claim.

## Deferred (extension points only)

A transport abstraction and async clients are deferred until an approved Control Plane or Community runtime API exists (ADR-003). No placeholder module is created for them.

## Decisions resolved (2026-11-24 alignment)

1. **Validator:** the SDK has no runtime dependency on kritva-sense. It carries its own hand-written validation against its vendored schema; the pinned kritva-sense validator, generator and conformance harness are test and CI oracles with cross-validation tests. Upstream is authoritative for contract semantics.
2. **Python and dependencies:** Python 3.12+; zero runtime dependencies in the first release; `jsonschema` test-only.
3. **Sense stream and frame-graph contracts:** approved and eligible, implemented in a later increment under KOS-SDK-005.

## Open decisions

Re-check PyPI availability of `kritva-sdk` before the first release (not listed on 2026-11-25; ADR-001). Further decisions arise as SDK-002 and SDK-003 are specified.
