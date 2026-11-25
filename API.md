# Kritva SDK Public API Design

**Status:** PROPOSED (SDK-001 design, aligned 2026-11-24; owner approval pending). No API below is implemented or stable.

## Scope of the first release

The first SDK release is a **contract-first Python library**: typed models and validators over approved, versioned upstream contract schemas. It is not a network client.

- Eligible contracts today, all from kritva-sense at pin tag `v0.2.0` (commit `543f5743d6ffd8fa1ed1ee5fdbf8295ae6a69a77`): the **Sense sample contract 0.1.0**, the **stream contract 0.1.0** and the **frame-graph contract 0.1.0** (all APPROVED). Approval makes a contract eligible, not implemented.
- Staging: the first increment implements the sample contract only; stream and frame-graph models follow under KOS-SDK-005, each with its own pin and conformance tests.
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

## Decisions resolved (2026-11-24 alignment)

1. **Validator:** the SDK has no runtime dependency on kritva-sense. It carries its own hand-written validation against its vendored schema; the pinned kritva-sense validator, generator and conformance harness are test and CI oracles with cross-validation tests. Upstream is authoritative for contract semantics.
2. **Python and dependencies:** Python 3.12+; zero runtime dependencies in the first release; `jsonschema` test-only.
3. **Sense stream and frame-graph contracts:** approved and eligible, implemented in a later increment under KOS-SDK-005.

## Open decisions

PyPI availability of `kritva-sdk` (to be checked directly, ADR-001). Further decisions arise as SDK-002 and SDK-003 are specified.
