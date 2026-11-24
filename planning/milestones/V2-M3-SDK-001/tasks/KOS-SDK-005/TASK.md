# KOS-SDK-005 — Implement Sense API Adapter

Status: PROPOSED / PLANNING_ONLY. Milestone: V2-M3-SDK-001. Narrowed on 2026-11-24; Motion, Mind and Skill moved to KOS-SDK-009.

Objective: provide a typed Python adapter for the approved Sense 0.1.0 contract, preserving Sense ownership and semantics.

In scope: contract inventory, adapter interface, version declaration, request/response models, error mapping and conformance tests against `contract/SENSE_CONTRACT.md` and `contract/sense-sample.schema.json`.

Out of scope: upstream contract changes, sensing engines, Motion, Mind and Skill adapters.

Dependencies: Sense 0.1.0 (APPROVED) pinned by exact commit SHA; SDK-003 client foundation.
