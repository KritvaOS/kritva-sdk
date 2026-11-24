# Kritva SDK Architecture

**Status:** PROPOSED — review required before implementation.

## Purpose and position
Kritva SDK is the application-facing Python client library for approved Kritva APIs. It is not a second runtime, service, orchestration engine or contract authority.

```text
Application
    |
Kritva SDK
    +-- Control Plane client (only after API/security approval)
    +-- Core / Robot client
    +-- Sense / Motion / Mind / Skill adapters
    +-- optional Simulation adapter
    +-- optional ROS 2 adapter
    |
Versioned upstream contracts and APIs
    |
Kritva runtime and platform
```

## Ownership
SDK owns public Python APIs, client construction/configuration/lifecycle, transport abstraction, typed models and errors, SDK-side validation, compatibility declarations, package distribution, examples and conformance tests.

SDK does not own canonical component schemas, authorization policy, Control Plane service, simulator, robot drivers, motor control or safety validation.

## Target package layout (SDK-002 onward)
```text
sdk/python/
  pyproject.toml
  src/kritva/
    __init__.py
    client.py
    config.py
    errors.py
    models/
    core/
    robot/
    sense/
    motion/
    mind/
    skill/
    control_plane/
    transports/
    adapters/
      ros2/          # optional extra
      simulation/    # optional extra
tests/{unit,contract,integration,regression}/
examples/{quickstart,robot_discovery,sense_stream,motion_command,skill_execution}/
docs/{api,guides}/
schemas/             # SDK-owned schemas only
```

Directories are introduced with their first real deliverable; no placeholder modules are required for this planning baseline.

## Design principles
1. High-level APIs are transport-independent.
2. Sync/async behavior and cancellation are explicit.
3. Timeouts, retries and idempotency follow upstream contracts.
4. Resource-owning clients have deterministic close/context-manager behavior.
5. Models preserve upstream units, timestamps, frame identifiers, lifecycle and error semantics.
6. Base install is lightweight; ROS 2 and simulation are optional.
7. Client validation never replaces server authorization or policy.
8. Python SDK makes no hard real-time or physical-safety guarantee.

## Versioning
SDK package SemVer is independent of upstream contract versions. Each adapter declares supported contract versions and rejects unsupported versions clearly. Breaking public API changes require a MAJOR version, migration notes and regression evidence.

## Open decisions for SDK-001
Public namespace; sync/async surface; initial transport/authentication; Control Plane API boundary; pinned upstream contract versions; supported Python versions; distribution/index strategy; optional ROS 2 and simulator adapter contracts.
