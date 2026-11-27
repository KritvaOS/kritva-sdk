# KOS-SDK-005 — Implement Sense API Adapter

Status: IN_PROGRESS from 2026-11-27 on the owner's authorization (approved plan scope, D-153); not in the frozen program baseline; not accepted; no weight or credit. Milestone: V2-M3-SDK-001. Narrowed on 2026-11-24; Motion, Mind and Skill moved to KOS-SDK-009.

Objective: provide typed Python adapters for the approved Sense contracts (sample 0.1.0 is implemented first under SDK-003; this task adds the approved stream 0.1.0 and frame-graph 0.1.0 contracts), preserving Sense ownership and semantics.

In scope: contract inventory, adapter interface, version declaration, request/response models, error mapping and conformance tests against `contract/STREAM_CONTRACT.md` with `contract/stream.schema.json` and `contract/FRAME_GRAPH_CONTRACT.md` with `contract/frame-transform.schema.json`, each pinned by tag and commit SHA.

Out of scope: upstream contract changes, sensing engines, Motion, Mind and Skill adapters.

Dependencies: Sense 0.1.0 (APPROVED) pinned by exact commit SHA; SDK-003 client foundation.
