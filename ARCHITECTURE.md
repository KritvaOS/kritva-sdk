# Kritva SDK Architecture

**Status:** PROPOSED — review required before implementation.

## Purpose and position
Kritva SDK is a contract-first Python library for approved Kritva contracts: typed models, validators, compatibility declarations and (later) clients. It is not a second runtime, service, orchestration engine or contract authority. The first release contains no network client, because no approved service API exists (Core R1.0 is an in-process C++ API; Control Plane and Sim are NOT_AVAILABLE).

```text
Application
    |
kritva_sdk (this repository)
    +-- config, errors, compat
    +-- sense   (Sense contract 0.1.0, first release)
    +-- [future, only with approved contracts] motion, mind, skill
    +-- [future extension points, none implemented] transport, Control Plane client,
        simulation adapter, ROS 2 adapter
    |
Vendored, pinned contract schemas (upstream owns them)
```

## Ownership
SDK owns public Python APIs, configuration, typed models and errors, SDK-side validation, compatibility declarations, packaging, examples and conformance tests.

SDK does not own canonical component schemas, authorization policy, the Control Plane service, the simulator, robot drivers, motor control or safety validation. Dependency direction is preserved: Mind and Motion -> Skill. The SDK consumes approved contracts and never reverses ownership.

## Schema ownership and validation flow
Contract schemas are **vendored as immutable snapshots**, never fetched at build or run time. Each snapshot records the upstream repository and path, approved version and tag, exact commit SHA, file checksum and approval status. A CI drift check compares each snapshot with its pinned upstream revision. Updating a schema is an explicit reviewed change.

Flow: payload -> contract-version check (`UNSUPPORTED_CONTRACT_VERSION` fails first) -> schema validation against the vendored snapshot -> typed model. Errors keep the upstream code.

## Target package layout (SDK-002 onward)
```text
pyproject.toml
release/              # pinned build requirements, sdist normaliser
src/kritva_sdk/
    __init__.py
    config.py
    errors.py
    compat.py
    sense/            # first release
    _schemas/         # vendored, pinned snapshots with a provenance manifest
tests/{unit,contract,regression}/
docs/
```
Directories are introduced with their first real deliverable. Motion, Mind and Skill packages appear only after their contracts are approved and tagged. Integration and transport directories are not created until an approved API exists.

## Design principles
1. The first release is transport-free; any later client is transport-independent.
2. Sync/async behavior and cancellation are explicit.
3. Timeouts, retries and idempotency follow upstream contracts once a network surface exists.
4. Resource-owning clients have deterministic close/context-manager behavior.
5. Models preserve upstream units, timestamps, frame identifiers, lifecycle and error semantics.
6. Base install is lightweight; ROS 2 and simulation are optional.
7. Client validation never replaces server authorization or policy.
8. Python SDK makes no hard real-time or physical-safety guarantee.

## Versioning
SDK package SemVer is independent of upstream contract versions. Each adapter declares supported contract versions and rejects unsupported versions clearly. Breaking public API changes require a MAJOR version, migration notes and regression evidence.

## Open decisions for SDK-001
Resolved: reuse of the kritva-sense validator (oracle only, no runtime dependency), Python 3.12+, Sense stream and frame-graph scope (later increment under SDK-005), namespace `kritva_sdk`, vendored pinned schemas, hand-written models, transport deferred. Still open: PyPI availability of `kritva-sdk`; the first network surface (Control Plane or a Community runtime API) and when it is approved; optional ROS 2 and simulator adapters.
