# Kritva SDK Public API Design

**Status:** PROPOSED (SDK-001 design, aligned 2026-11-24; owner approval pending). No API below is implemented or stable.

## Scope of the first release

The first SDK release is a **contract-first Python library**: typed models and validators over approved, versioned upstream contract schemas. It is not a network client.

- Eligible contract today: **Sense contract 0.1.0** (APPROVED; pin tag `v0.2.0`, commit `543f5743d6ffd8fa1ed1ee5fdbf8295ae6a69a77`).
- Explicitly excluded until their contracts are approved and versioned: Mind, Motion, Skill, Sim, Control Plane.
- Explicitly excluded: any Core client (Core R1.0 is an in-process C++ API with no Python or network surface), any HTTP or other network implementation, any ROS 2 or simulator adapter.

Distribution name `kritva-sdk`, import namespace `kritva_sdk` (ADR-001). Availability on PyPI is not yet confirmed.

## Candidate public surface (illustrative, not stable)

```python
from kritva_sdk import SdkConfig, supported_contracts
from kritva_sdk.sense import SenseSample, validate_sample, parse_sample
from kritva_sdk.errors import ContractError, UnsupportedContractVersion

supported_contracts()            # {"sense": ("0.1.0",)}
sample = parse_sample(payload)   # raises ContractError subclasses with upstream error codes
validate_sample(payload)         # schema validation without building a model
```

| Area | Responsibility | Authority |
|---|---|---|
| `kritva_sdk.config` | Explicit, validated, immutable configuration | SDK |
| `kritva_sdk.errors` | Typed errors that preserve upstream codes (for example `UNSUPPORTED_CONTRACT_VERSION`, `UNKNOWN_FIELD`, `INVALID_SENSOR_ID`, `INVALID_TIMESTAMP`) | SDK, codes from the contract |
| `kritva_sdk.compat` | Supported-contract declarations and version checks that fail before any operation | SDK |
| `kritva_sdk.sense` | Typed sample models, parse and validate, serialization | kritva-sense (normative schema), SDK (Python surface) |

Models are hand-written and typed. The vendored JSON Schema stays normative; conformance tests prove that model serialization and validation agree with it. Generated code is not the public API in the first release.

## Behavior rules

- Units, timestamps (`clock`, `unit`, `value`), frame identifiers, `validity` and `error_code` semantics are preserved exactly as the contract defines them; no conversion is hidden.
- Unknown fields are rejected, as the contract requires. Unsupported contract versions fail clearly and early.
- Validation is synchronous and pure (no I/O); it is safe to call from async code. No timeout or cancellation semantics are needed until a network surface exists.
- The base import has no dependency on ROS 2, a simulator, hardware or a network library.
- Client-side validation never replaces server-side authorization or safety checks. Nothing here makes a real-time or physical-safety claim.

## Deferred (extension points only)

A transport abstraction and async clients are deferred until an approved Control Plane or Community runtime API exists (ADR-003). No placeholder module is created for them.

## Open decisions

1. Whether `kritva_sdk.sense` reuses the kritva-sense reference validator as a dependency or carries its own validator checked against the same schema. The SDK must not fork contract semantics.
2. Handling of the Sense stream and frame-graph contracts, which are separate documents in kritva-sense and not covered by this scope.
3. Python version matrix (3.11+ proposed) and the validation library (for example `jsonschema`), subject to dependency review.
