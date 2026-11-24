# KOS-SDK-009 — Acceptance Criteria

Status: PROPOSED / PLANNING_ONLY.

1. Each adapter pins an APPROVED upstream contract version and commit SHA; no draft contract is pinned.
2. Adapters preserve upstream ownership and semantics, and the Mind and Motion → Skill dependency direction.
3. Typed models, deterministic error mapping, timeout and cancellation tests exist per adapter.
4. Conformance tests run on the exact commit; any gate not implemented is reported NOT_IMPLEMENTED.
5. No SDK-only substitute for a missing upstream contract is introduced.
