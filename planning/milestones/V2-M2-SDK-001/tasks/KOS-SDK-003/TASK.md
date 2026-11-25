# KOS-SDK-003 — Implement Configuration, Contract Compatibility and Sense Models

Status: PROPOSED / PLANNING_ONLY. Milestone: V2-M2-SDK-001. Rescoped 2026-11-24: the Core client was removed because Core R1.0 has no Python or network surface.

Objective: implement explicit configuration, typed errors, contract-version compatibility declarations and typed Sense 0.1.0 models and validation over vendored, pinned schemas.

In scope: configuration validation, error model preserving upstream codes, supported-contract declarations, vendored schema snapshots with provenance and a drift check, hand-written Sense models, conformance and negative tests.

Out of scope: any network client or transport, Core, Control Plane, Mind, Motion, Skill and Sim adapters, capability business logic, robot safety.

Dependencies: SDK-001 and SDK-002 approval; Sense contract 0.1.0 (APPROVED) at tag `v0.2.0`, commit `543f5743d6ffd8fa1ed1ee5fdbf8295ae6a69a77`.
