# Kritva SDK Milestone Status

**Status:** planning snapshot, not central acceptance. KOS-SDK-001 to 003 are complete in this repository with the owner's decision to accept (2026-11-26, interim D-047, not independent); program acceptance, baseline and approval records are pending and no milestone is closed. KOS-SDK-004 to 009 are approved plan scope (D-153), not started.

| Milestone | Tasks | Status | Main dependency |
|---|---|---|---|
| V2-M1-SDK-001 | KOS-SDK-001 | TASKS COMPLETE, acceptance pending | Owner architecture/API review |
| V2-M2-SDK-001 | KOS-SDK-002/003 | TASKS COMPLETE, acceptance pending | M1 approval; package decisions |
| V2-M3-SDK-001 | KOS-SDK-004/005 | APPROVED_PLAN, NOT_STARTED | Control Plane and capability contracts |
| V2-M5-SDK-001 | KOS-SDK-006 | APPROVED_PLAN, NOT_STARTED | Simulation contract |
| V2-M7-SDK-001 | KOS-SDK-007 | APPROVED_PLAN, NOT_STARTED | Telemetry/result contracts |
| V2-M8-SDK-001 | KOS-SDK-008 | APPROVED_PLAN, NOT_STARTED | Security and release evidence |

Gates `make check`, `lint`, `test-integration`, `test-regression`, `docs-check` and `acceptance` are NOT_IMPLEMENTED and block program acceptance until implemented or dispositioned; no gate is reported as passing beyond `make test-unit`, `make packaging-test`, `make schema-drift` and `make conformance-test`.
