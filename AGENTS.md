# Kritva SDK Engineering Agent Instructions

## Authority
- The project owner decides architecture, scope, compatibility promises, security posture and releases. AI agents provide advice and evidence only.
- Follow approved KritvaOS architecture and contracts owned by their respective repositories.
- `kritva-program` owns central decisions, baseline, approvals, gate closures and V2 program status.
- A local proposal is not an approved program task or milestone.

## SDK boundary
SDK owns Python developer APIs, client ergonomics, configuration, lifecycle, transport adapters, SDK-side typing/validation, contract compatibility declarations, packaging, examples and documentation.

SDK does not own or redefine Core, Sense, Motion, Mind or Skill contracts; Control Plane service implementation or authorization policy; simulator implementation; hardware drivers; motion-control loops; robot safety policy; or physical validation.

If an upstream contract is missing or unclear, raise the change with its owning repository. Do not invent an SDK-only substitute.

## API-first workflow
Before implementation: identify task and upstream contract; record exact contract version/commit; define public API and error semantics; document sync/async, timeout and cancellation behavior; assess security/dependencies; define tests; implement; run gates; record immutable evidence.

## Python-first rules
- Python is the first SDK language. C++ bindings and language parity are deferred.
- Base SDK import must not require ROS 2, simulator or hardware.
- Keep integrations optional and isolated behind adapters/extras.
- Public APIs must have typed inputs/outputs and deterministic errors.
- Async cancellation, timeout and cleanup semantics must be explicit.
- Do not claim hard real-time guarantees from Python.

## Contracts and dependencies
Consume approved versioned upstream contracts; do not fork their schemas. Pin supported versions before implementing adapters. Review necessity, license, security, portability and maintenance of every dependency. Client validation never replaces server authorization or safety checks.

## Testing and evidence
Use unit, contract, integration and regression tests as appropriate. Simulation is labelled simulation and is never physical or safety validation. Do not claim tests passed unless run on the exact commit. Record commit SHAs and CI run IDs. An unimplemented gate is NOT_IMPLEMENTED, never PASS.

## Program governance
- Follow the Kritva V2 acceptance standard and task-ID convention.
- The SDK workstream is registered centrally (D-149). Local task status never creates credit: KOS-SDK-001 to 003 are complete with program acceptance pending, KOS-SDK-004 to 009 are approved plan scope (D-153), not started.
- Never modify central baseline, approvals, gate closures, workstreams or generated program views from this repository.
- A local merge, tag or CI pass does not close a central milestone.

## Git and security
Work on branches and PRs; do not push directly to main. Use `type(scope): summary` and exactly one `Task:` or `Tasks:` footer. Use `Tasks: None (reason)` only for docs/chore commits implementing no task. Do not add AI-session trailers. Never commit credentials, tokens, private keys, production or personal data. Use fake example values and follow SECURITY.md.

> Understand and preserve upstream contract boundaries before changing the SDK.
