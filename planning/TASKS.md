# Kritva SDK Task Register

**Classification:** PLANNING_ONLY. KOS-SDK-001 to 003 are complete in this repository and the owner decided on 2026-11-26 to accept them (interim D-047 review, not independent); KOS-SDK-001 to 003 are in the frozen program baseline v16 (D-155) and credited by the program; credit decisions stay with kritva-program. KOS-SDK-005 started 2026-11-27 on the owner's authorization, is implemented and merged (pull requests 17 to 20, main 3505859) and is in the frozen program baseline v17 (D-161, weight 5): no credit or acceptance applies until kritva-program records the owner's approval, and its manual acceptance criteria still need the owner's recorded review. KOS-SDK-004 and 006 to 009 are approved plan scope (D-153), not started, not accepted.

| Task ID | Title | Local milestone | Status | Dependency |
|---|---|---|---|---|
| KOS-SDK-001 | Define Python-first SDK architecture and developer API | V2-M1-SDK-001 | COMPLETE, owner decision to accept 2026-11-26 (interim D-047, not independent); program acceptance pending | capability contract review |
| KOS-SDK-002 | Establish Python package foundation and reproducible build | V2-M2-SDK-001 | COMPLETE, owner decision to accept 2026-11-26 (interim D-047, not independent); program acceptance pending | SDK-001 approval |
| KOS-SDK-003 | Implement configuration, contract compatibility and Sense models | V2-M2-SDK-001 | COMPLETE, owner decision to accept 2026-11-26 (interim D-047, not independent); program acceptance pending | SDK-001/002; Sense 0.1.0 (APPROVED) |
| KOS-SDK-004 | Define and implement Control Plane client adapter | V2-M3-SDK-001 | APPROVED_PLAN, NOT_STARTED (D-153; conditional on its upstream contracts; no credit) | approved Control Plane API/security |
| KOS-SDK-005 | Implement Sense API adapter | V2-M3-SDK-001 | COMPLETE (implemented and merged, main 3505859; in program baseline v17, D-161); program acceptance pending; manual criteria pending owner review; no credit yet | Sense 0.1.0 (APPROVED); SDK-003 |
| KOS-SDK-006 | Add simulation adapter and executable examples | V2-M5-SDK-001 | APPROVED_PLAN, NOT_STARTED (D-153; conditional on its upstream contracts; no credit) | approved simulation contract |
| KOS-SDK-007 | Add telemetry, event and result interfaces | V2-M7-SDK-001 | APPROVED_PLAN, NOT_STARTED (D-153; conditional on its upstream contracts; no credit) | approved telemetry/result contracts |
| KOS-SDK-009 | Implement Motion, Mind and Skill adapters | V2-M3-SDK-001 | APPROVED_PLAN, NOT_STARTED (D-153; conditional on its upstream contracts; no credit) | approved, tagged Motion/Mind/Skill contracts (currently DRAFT/PROPOSED) |
| KOS-SDK-008 | Complete security, compatibility and release readiness | V2-M8-SDK-001 | APPROVED_PLAN, NOT_STARTED (D-153; conditional on its upstream contracts; no credit) | previous milestones |

IDs are stable and not reusable. Each task has a task definition and criteria. Local status does not create program credit.
