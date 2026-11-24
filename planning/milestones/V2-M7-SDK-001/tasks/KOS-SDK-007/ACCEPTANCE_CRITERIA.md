# Acceptance Criteria — KOS-SDK-007

| ID | Criterion | Verification |
|---|---|---|
| AC-001 | Models match approved upstream schemas and versions. | contract tests |
| AC-002 | Stream lifecycle, termination, stale data and errors are deterministic. | unit/contract tests |
| AC-003 | Reconnection/retry is bounded and contract-compliant. | integration tests |
| AC-004 | Results retain upstream correlation identifiers where available. | integration tests |
| AC-005 | Software evidence is reproducible and scoped. | test report |
| AC-006 | Software telemetry does not imply physical validation. | review |
